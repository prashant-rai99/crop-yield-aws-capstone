"""
Trains a crop yield forecasting model using historical Indian agricultural data
(1997-2020) sourced from Kaggle. The trained model predicts Yield given
Crop, Season, State, Crop_Year, Area, Annual_Rainfall, Fertilizer, and Pesticide.

This is an OFFLINE training script. It is not part of the live Flask app -
it is run once (or re-run when the dataset is updated) to produce a
forecast_model.pkl file, which the Flask app loads at runtime for predictions.

Usage:
    python train_forecast_model.py
"""

import pandas as pd
import joblib
import json
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error

DATA_PATH = Path("ml/data/crop_yield.csv")
MODEL_OUTPUT_PATH = Path("ml/models/forecast_model.pkl")
METADATA_OUTPUT_PATH = Path("ml/models/forecast_metadata.json")
AVERAGES_OUTPUT_PATH = Path("ml/models/forecast_averages.json")
HISTORY_OUTPUT_PATH = Path("ml/models/forecast_history.json")

CATEGORICAL_COLUMNS = ["Crop", "Season", "State"]
NUMERIC_COLUMNS = ["Crop_Year", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"]
TARGET_COLUMN = "Yield"

# Year cutoff for a time-based train/test split (train on the past, test on
# more recent years - this mirrors how the model will actually be used).
TEST_YEAR_CUTOFF = 2016


def load_and_clean_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # The raw Kaggle CSV has trailing whitespace in text columns
    # (e.g. "Kharif     " instead of "Kharif") - strip it.
    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].astype(str).str.strip()

    return df


def encode_categoricals(df: pd.DataFrame, encoders: dict = None):
    """Label-encodes categorical columns. Reuses fitted encoders if provided,
    otherwise fits new ones (used at training time)."""
    df = df.copy()
    fitted = encoders is None
    if encoders is None:
        encoders = {}

    for col in CATEGORICAL_COLUMNS:
        if fitted:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le
        else:
            le = encoders[col]
            df[col] = le.transform(df[col])

    return df, encoders


AVERAGED_COLUMNS = ["Annual_Rainfall", "Fertilizer", "Pesticide", "Area"]


def build_averages_lookup(df: pd.DataFrame) -> dict:
    """Builds a multi-level fallback lookup of historical average values for
    Rainfall/Fertilizer/Pesticide/Area, used to auto-fill technical inputs a
    farmer wouldn't know when requesting a future prediction. Falls back from
    the most specific grouping to the most general if a combination has no
    (or very little) historical data."""

    def grouped_means(group_cols):
        g = df.groupby(group_cols)[AVERAGED_COLUMNS].mean()
        return {
            (k if isinstance(k, tuple) else (k,)): {col: round(v, 2) for col, v in row.items()}
            for k, row in zip(g.index, g.to_dict("records"))
        }

    return {
        "by_crop_state_season": {
            "|".join(k): v for k, v in grouped_means(["Crop", "State", "Season"]).items()
        },
        "by_crop_season": {
            "|".join(k): v for k, v in grouped_means(["Crop", "Season"]).items()
        },
        "by_crop": {
            "|".join(k): v for k, v in grouped_means(["Crop"]).items()
        },
        "global": {col: round(df[col].mean(), 2) for col in AVERAGED_COLUMNS},
    }


def build_yield_history(df: pd.DataFrame) -> dict:
    """Builds a year-wise historical Yield trend lookup for charting on the
    forecast page (actual past yield next to the predicted future value).
    Same multi-level fallback as the averages lookup: exact crop+state+season
    combo first, then crop+season (averaged across states), then crop alone."""

    def series_for(group_cols):
        g = df.groupby(group_cols + ["Crop_Year"])["Yield"].mean().reset_index()
        result = {}
        for key, sub in g.groupby(group_cols):
            key_tuple = key if isinstance(key, tuple) else (key,)
            points = sorted(
                [{"year": int(r.Crop_Year), "yield": round(r.Yield, 3)} for r in sub.itertuples()],
                key=lambda p: p["year"],
            )
            result["|".join(key_tuple)] = points
        return result

    return {
        "by_crop_state_season": series_for(["Crop", "State", "Season"]),
        "by_crop_season": series_for(["Crop", "Season"]),
        "by_crop": series_for(["Crop"]),
    }


def main():
    print(f"Loading dataset from {DATA_PATH} ...")
    df = load_and_clean_data(DATA_PATH)
    print(f"Loaded {len(df)} rows, {df['Crop'].nunique()} crops, "
          f"{df['State'].nunique()} states, years {df['Crop_Year'].min()}-{df['Crop_Year'].max()}")

    # Time-based split: train on years before the cutoff, test on the rest.
    train_df = df[df["Crop_Year"] < TEST_YEAR_CUTOFF]
    test_df = df[df["Crop_Year"] >= TEST_YEAR_CUTOFF]
    print(f"Train rows: {len(train_df)} (years < {TEST_YEAR_CUTOFF}), "
          f"Test rows: {len(test_df)} (years >= {TEST_YEAR_CUTOFF})")

    # Fit label encoders on the FULL dataset's category vocabulary (Crop,
    # Season, State are a fixed set of names, not something that should
    # differ between train/test - e.g. a crop that only appears in test
    # years still needs a valid encoding). Only the regression model itself
    # is trained on the time-based train split below.
    _, encoders = encode_categoricals(df)
    train_encoded, _ = encode_categoricals(train_df, encoders=encoders)
    test_encoded, _ = encode_categoricals(test_df, encoders=encoders)

    feature_columns = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS
    X_train = train_encoded[feature_columns]
    y_train = train_encoded[TARGET_COLUMN]
    X_test = test_encoded[feature_columns]
    y_test = test_encoded[TARGET_COLUMN]

    print("Training RandomForestRegressor ...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5
    r2 = r2_score(y_test, predictions)

    # MAPE is scale-independent, unlike MAE/RMSE - Yield varies from ~0.2 to
    # 5000+ across crops, so raw MAE/RMSE alone would be dominated by
    # high-yield crops and are misleading without this context.
    # A small number of rows have Yield == 0 (likely crop-failure or
    # negligible-production cases) - these make percentage error undefined,
    # so they are excluded from MAPE only (not from MAE/RMSE/R2 above).
    non_zero_mask = y_test > 0.01
    excluded_count = (~non_zero_mask).sum()
    y_test_nz = y_test[non_zero_mask]
    preds_nz = predictions[non_zero_mask]
    mape = mean_absolute_percentage_error(y_test_nz, preds_nz)
    # Median APE is far more robust than mean MAPE here: a handful of rows
    # (e.g. a crop grown negligibly in a state in a given year, actual
    # yield near-zero) produce percentage errors in the thousands and
    # heavily skew the mean. Median is the honest number to report.
    ape = (abs(y_test_nz - preds_nz) / y_test_nz) * 100
    median_ape = np.median(ape)

    print("\n--- Evaluation on held-out years (%d-2020) ---" % TEST_YEAR_CUTOFF)
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"Mean MAPE:   {mape * 100:.2f}% (skewed by rare low-yield outliers)")
    print(f"Median APE:  {median_ape:.2f}% (robust, recommended metric to report)")
    print(f"({excluded_count} near-zero-yield rows excluded from these percentage metrics)")
    print(f"R2:   {r2:.4f}")

    # Feature importance - useful for the resume/portfolio writeup.
    importances = dict(zip(feature_columns, model.feature_importances_))
    print("\nFeature importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.4f}")

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": model,
        "encoders": encoders,
        "feature_columns": feature_columns,
    }
    joblib.dump(bundle, MODEL_OUTPUT_PATH)
    print(f"\nSaved model bundle to {MODEL_OUTPUT_PATH}")

    # The live Flask form only asks the user for Crop/Season/State/Year/Area -
    # not Annual_Rainfall/Fertilizer/Pesticide, since a farmer forecasting a
    # future season has no way to know those values in advance. Instead, we
    # precompute historical averages here (from the full dataset, all years)
    # so the app can look them up at request time with no CSV/pandas needed
    # in production. Three fallback levels handle combinations that are rare
    # or missing at the most specific level.
    print("\nComputing historical averages for Rainfall/Fertilizer/Pesticide lookups ...")
    avg_cols = ["Annual_Rainfall", "Fertilizer", "Pesticide"]

    def build_avg_dict(group_cols):
        grouped = df.groupby(group_cols)[avg_cols].mean().round(2)
        result = {}
        for key, row in grouped.iterrows():
            if not isinstance(key, tuple):
                key = (key,)
            d = result
            for part in key[:-1]:
                d = d.setdefault(part, {})
            d[key[-1]] = {col: row[col] for col in avg_cols}
        return result

    averages_by_crop_season_state = build_avg_dict(["Crop", "Season", "State"])
    averages_by_crop_season = build_avg_dict(["Crop", "Season"])
    averages_by_crop = build_avg_dict(["Crop"])
    overall_averages = {col: round(df[col].mean(), 2) for col in avg_cols}

    metadata = {
        "trained_on_rows": len(train_df),
        "tested_on_rows": len(test_df),
        "test_year_cutoff": TEST_YEAR_CUTOFF,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mean_mape_percent": round(mape * 100, 2),
        "median_ape_percent": round(median_ape, 2),
        "mape_excluded_near_zero_rows": int(excluded_count),
        "r2": round(r2, 4),
        "feature_importances": {k: round(v, 4) for k, v in importances.items()},
        "available_crops": sorted(df["Crop"].unique().tolist()),
        "available_seasons": sorted(df["Season"].unique().tolist()),
        "available_states": sorted(df["State"].unique().tolist()),
        "year_range": [int(df["Crop_Year"].min()), int(df["Crop_Year"].max())],
        "averages_by_crop_season_state": averages_by_crop_season_state,
        "averages_by_crop_season": averages_by_crop_season,
        "averages_by_crop": averages_by_crop,
        "overall_averages": overall_averages,
    }
    with open(METADATA_OUTPUT_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {METADATA_OUTPUT_PATH}")

    averages = build_averages_lookup(df)
    with open(AVERAGES_OUTPUT_PATH, "w") as f:
        json.dump(averages, f, indent=2)
    print(f"Saved historical averages lookup to {AVERAGES_OUTPUT_PATH}")

    history = build_yield_history(df)
    with open(HISTORY_OUTPUT_PATH, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Saved yield history lookup to {HISTORY_OUTPUT_PATH}")


if __name__ == "__main__":
    main()