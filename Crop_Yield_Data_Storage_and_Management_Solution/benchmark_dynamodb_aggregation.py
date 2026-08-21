"""
Benchmark: compute season-wise record count and average yield directly
from DynamoDB (full table scan + client-side Python aggregation), timed
end-to-end. This is compared against the equivalent Athena SQL query
(GROUP BY season) measured separately in the Athena console, to show
the latency difference between querying a data lake (S3 + Athena) vs
running the same aggregation against the live operational database.

Usage:
    python benchmark_dynamodb_aggregation.py
"""

import time
from collections import defaultdict
from decimal import Decimal

import boto3

AWS_REGION = "us-east-1"
DYNAMODB_TABLE_NAME = "CropYield_Data"


def scan_all_items(table):
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


def aggregate_by_season(items):
    totals = defaultdict(lambda: {"count": 0, "yield_sum": Decimal(0)})

    for item in items:
        season = item.get("season", "Unknown")
        yield_amount = item.get("YieldAmount", Decimal(0))
        totals[season]["count"] += 1
        totals[season]["yield_sum"] += yield_amount

    results = {}
    for season, data in totals.items():
        avg_yield = data["yield_sum"] / data["count"] if data["count"] else Decimal(0)
        results[season] = {
            "count": data["count"],
            "avg_yield": round(float(avg_yield), 2),
        }

    return results


def main():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    print("Starting benchmark: DynamoDB scan + Python aggregation...")
    start_time = time.time()

    items = scan_all_items(table)
    results = aggregate_by_season(items)

    elapsed = time.time() - start_time

    print(f"\nTotal records scanned: {len(items)}")
    print("Season-wise results:")
    for season, data in sorted(results.items(), key=lambda x: -x[1]["count"]):
        print(f"  {season}: {data['count']} records, avg_yield={data['avg_yield']}")

    print(f"\nTotal elapsed time (scan + aggregation): {elapsed:.3f} seconds")


if __name__ == "__main__":
    main()