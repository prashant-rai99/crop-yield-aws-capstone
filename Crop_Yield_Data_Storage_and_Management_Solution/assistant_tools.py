"""
Phase 6: Tool functions for the LLM-powered agentic query assistant.

Each function here is a "tool" that the Gemini assistant can choose to call
based on a farmer's or admin's natural-language question. These functions
reuse the exact same DynamoDB / Athena / ML access patterns already used
elsewhere in the app (dashboard route, Athena pipeline, forecast route) —
no new data-access logic is introduced here.

This module is imported by app_aws.py; it does not run standalone.
"""

from boto3.dynamodb.conditions import Key


def query_yield_data(yield_table, user_email: str, season: str = None) -> dict:
    """
    Fetch the logged-in farmer's own yield records from DynamoDB.

    Reuses the same query pattern as the /dashboard route: a direct
    Table.query() on the UserEmail primary key (fast, no scan).

    Args:
        yield_table: the boto3 DynamoDB Table resource for CropYield_Data
                     (passed in from app_aws.py, not created here).
        user_email: the logged-in user's email — always taken from the
                     Flask session server-side, never from the LLM, so a
                     farmer can only ever see their own records.
        season: optional season name (e.g. "Kharif") to filter results
                to. If omitted, returns all of the farmer's records.

    Returns:
        A dict with the farmer's records and simple summary stats, in a
        compact form suitable for handing back to the LLM as a tool result.
    """
    res = yield_table.query(KeyConditionExpression=Key("UserEmail").eq(user_email))
    raw_yields = res.get("Items", [])

    records = [
        {
            "crop_name": r.get("crop_name", ""),
            "season": r.get("season", ""),
            "yield_amount": float(r.get("YieldAmount", 0)),
            "area": float(r.get("Area", 0)),
            "date": r.get("CreatedAt", ""),
        }
        for r in raw_yields
    ]

    if season:
        records = [r for r in records if r["season"].lower() == season.lower()]

    total_production = sum(r["yield_amount"] for r in records)
    total_area = sum(r["area"] for r in records)

    return {
        "record_count": len(records),
        "total_production": round(total_production, 2),
        "total_area": round(total_area, 2),
        "average_yield_per_hectare": (
            round(total_production / total_area, 2) if total_area > 0 else 0
        ),
        "records": records,
    }


# Gemini function-calling schema for this tool.
# Note: user_email is deliberately NOT exposed here — it's injected
# server-side from the session, so the LLM can never ask for someone
# else's data.
QUERY_YIELD_DATA_DECLARATION = {
    "name": "query_yield_data",
    "description": (
        "Get the logged-in farmer's own crop yield records from the database. "
        "Use this for questions about the user's personal yield history, "
        "such as 'how much did I produce last season' or 'show my wheat records'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "season": {
                "type": "string",
                "description": (
                    "Optional. Filter to a specific season, e.g. Kharif, "
                    "Rabi, or Zaid. Omit to get all of the farmer's records."
                ),
            }
        },
        "required": [],
    },
}


# =====================================================================
# TOOL 2: get_analytics — aggregate stats across ALL farmers, via Athena
# =====================================================================

import time


def get_analytics(athena_client, group_by: str = "season") -> dict:
    """
    Run an aggregate query over the whole platform's yield data (all
    farmers) via Athena, reusing the same S3 data lake pipeline built in
    Phase 4 (export_to_s3.py -> crop_yield_db.yield_data table).

    Unlike query_yield_data, this deliberately has no per-user filter —
    it's meant for platform-wide questions, which is why it's the tool
    an admin would typically reach for.

    Args:
        athena_client: boto3 Athena client (passed in from app_aws.py).
        group_by: either "season" or "crop_name" — which column to
                  aggregate by. Defaults to "season".

    Returns:
        A dict with one row per group: record count, average yield per
        hectare, and total production.
    """
    if group_by not in ("season", "crop_name"):
        group_by = "season"

    query = f"""
        SELECT
            {group_by} AS group_value,
            COUNT(*) AS record_count,
            ROUND(AVG(yieldamount / NULLIF(area, 0)), 2) AS avg_yield_per_hectare,
            ROUND(SUM(yieldamount), 2) AS total_production
        FROM crop_yield_db.yield_data
        GROUP BY {group_by}
        ORDER BY total_production DESC
    """

    query_execution_id = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": "crop_yield_db"},
        ResultConfiguration={
            "OutputLocation": "s3://crop-yield-datalake-982515248045/athena-query-results/"
        },
    )["QueryExecutionId"]

    # Poll until the query finishes (Athena queries are async)
    for _ in range(20):  # ~20 second safety cap
        status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)[
            "QueryExecution"
        ]["Status"]["State"]

        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    if status != "SUCCEEDED":
        return {"error": f"Athena query did not succeed (status: {status})"}

    result = athena_client.get_query_results(QueryExecutionId=query_execution_id)
    rows = result["ResultSet"]["Rows"]

    # First row is the header row — skip it
    data_rows = rows[1:]
    groups = [
        {
            "group": row["Data"][0].get("VarCharValue", ""),
            "record_count": int(row["Data"][1].get("VarCharValue", 0)),
            "avg_yield_per_hectare": float(row["Data"][2].get("VarCharValue", 0)),
            "total_production": float(row["Data"][3].get("VarCharValue", 0)),
        }
        for row in data_rows
    ]

    return {"grouped_by": group_by, "results": groups}


GET_ANALYTICS_DECLARATION = {
    "name": "get_analytics",
    "description": (
        "Get platform-wide aggregate crop yield statistics across ALL farmers "
        "(not just the logged-in user). Use this for questions like 'which "
        "season has the best average yield overall' or 'what crop is grown "
        "the most'. This is the tool an admin would typically need."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "group_by": {
                "type": "string",
                "description": (
                    "Which field to group the aggregate by: 'season' or "
                    "'crop_name'. Defaults to 'season' if not specified."
                ),
            }
        },
        "required": [],
    },
}


# =====================================================================
# TOOL 3: predict_yield — wraps the Phase 5 ML forecast model
# =====================================================================


def predict_yield(
    forecast_bundle,
    get_technical_averages_fn,
    crop: str,
    season: str,
    state: str,
    year: int,
    area: float,
) -> dict:
    """
    Predict crop yield using the same trained RandomForestRegressor and
    feature-engineering pipeline as the /forecast page (Phase 5).

    Args:
        forecast_bundle: the loaded model bundle dict (model, encoders,
                          feature_columns) — passed in from app_aws.py,
                          same object /forecast already uses.
        get_technical_averages_fn: the existing get_technical_averages()
                          function from app_aws.py, passed in so this
                          module doesn't need to duplicate that lookup logic.
        crop, season, state: must match values the model was trained on
                          (see forecast_metadata.json's available_crops /
                          available_seasons / available_states).
        year: the crop year to predict for.
        area: farm area in hectares.

    Returns:
        A dict with the predicted yield per hectare and estimated total
        production, or an error dict if the inputs aren't valid for the model.
    """
    try:
        model = forecast_bundle["model"]
        encoders = forecast_bundle["encoders"]
        feature_columns = forecast_bundle["feature_columns"]

        technical = get_technical_averages_fn(crop, state, season)

        row = {
            "Crop": encoders["Crop"].transform([crop])[0],
            "Season": encoders["Season"].transform([season])[0],
            "State": encoders["State"].transform([state])[0],
            "Crop_Year": year,
            "Area": area,
            "Annual_Rainfall": technical["Annual_Rainfall"],
            "Fertilizer": technical["Fertilizer"],
            "Pesticide": technical["Pesticide"],
        }

        import pandas as pd

        X = pd.DataFrame([row])[feature_columns]
        predicted_yield = float(model.predict(X)[0])

        return {
            "crop": crop,
            "season": season,
            "state": state,
            "year": year,
            "area": area,
            "predicted_yield_per_hectare": round(predicted_yield, 3),
            "estimated_total_production": round(predicted_yield * area, 2),
        }
    except Exception as e:
        # Broadened from (KeyError, ValueError) to Exception, and now
        # prints the real error + inputs to the server terminal — the
        # narrower catch was hiding the actual failure reason during
        # debugging. Once this is confirmed stable, this can be
        # narrowed back down if desired.
        print(f"predict_yield error: {e!r}")
        print(
            f"  called with: crop={crop!r}, season={season!r}, state={state!r}, year={year!r}, area={area!r}"
        )
        return {
            "error": (
                f"Could not generate a prediction — '{crop}', '{season}', or "
                f"'{state}' may not be a value the model recognizes. ({e})"
            )
        }


PREDICT_YIELD_DECLARATION = {
    "name": "predict_yield",
    "description": (
        "Predict future crop yield for a given crop, season, state, year, "
        "and farm area, using the trained forecasting model. Use this for "
        "questions like 'what will my wheat yield be next season' or "
        "'predict yield for rice in Punjab in 2025 on 3 hectares'. "
        "If the user doesn't specify area, ask them for it rather than "
        "guessing — the prediction scales directly with area."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "crop": {"type": "string", "description": "Crop name, e.g. Wheat, Rice."},
            "season": {"type": "string", "description": "Season, e.g. Kharif, Rabi."},
            "state": {"type": "string", "description": "Indian state name."},
            "year": {"type": "integer", "description": "Crop year to predict for."},
            "area": {"type": "number", "description": "Farm area in hectares."},
        },
        "required": ["crop", "season", "state", "year", "area"],
    },
}
