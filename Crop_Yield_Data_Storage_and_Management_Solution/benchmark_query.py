"""
Benchmark script comparing two approaches to fetching yield records
for a specific season from CropYield_Data:

  1. "Before"  - scan() the whole table, then filter client-side for
                 season == TARGET_SEASON (this is what the admin
                 dashboard currently does).
  2. "After"   - query() the SeasonIndex GSI directly for
                 season == TARGET_SEASON (no client-side filtering,
                 no full-table read).

This produces a real, measured latency-improvement percentage that
can be used honestly in a resume line, instead of a made-up number.

Usage:
    python benchmark_query.py
"""

import boto3
import time
import statistics

REGION = "us-east-1"
NUM_RUNS = 5
TARGET_SEASON = "Kharif"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
yield_table = dynamodb.Table("CropYield_Data")


def run_scan_and_filter():
    """Old approach: scan the whole table, filter for season in Python."""
    start = time.perf_counter()

    matching_items = []
    response = yield_table.scan()
    matching_items.extend(
        item for item in response.get("Items", [])
        if item.get("season") == TARGET_SEASON
    )

    while "LastEvaluatedKey" in response:
        response = yield_table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        matching_items.extend(
            item for item in response.get("Items", [])
            if item.get("season") == TARGET_SEASON
        )

    elapsed = time.perf_counter() - start
    return elapsed, len(matching_items)


def run_gsi_query():
    """New approach: query the SeasonIndex GSI directly for the season."""
    start = time.perf_counter()

    matching_items = []
    response = yield_table.query(
        IndexName="SeasonIndex",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("season").eq(TARGET_SEASON)
    )
    matching_items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = yield_table.query(
            IndexName="SeasonIndex",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("season").eq(TARGET_SEASON),
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        matching_items.extend(response.get("Items", []))

    elapsed = time.perf_counter() - start
    return elapsed, len(matching_items)


def main():
    print(f"Comparing scan()+filter vs query() via SeasonIndex for season='{TARGET_SEASON}'")
    print(f"Running {NUM_RUNS} passes of each approach...\n")

    scan_timings = []
    query_timings = []
    scan_count = 0
    query_count = 0

    print("--- scan() + client-side filter (BEFORE) ---")
    for run_number in range(1, NUM_RUNS + 1):
        elapsed, count = run_scan_and_filter()
        scan_timings.append(elapsed)
        scan_count = count
        print(f"  Run {run_number}: {elapsed:.3f} seconds ({count} matching items)")

    print("\n--- query() via SeasonIndex GSI (AFTER) ---")
    for run_number in range(1, NUM_RUNS + 1):
        elapsed, count = run_gsi_query()
        query_timings.append(elapsed)
        query_count = count
        print(f"  Run {run_number}: {elapsed:.3f} seconds ({count} matching items)")

    scan_avg = statistics.mean(scan_timings)
    query_avg = statistics.mean(query_timings)

    if scan_count != query_count:
        print(
            f"\nWARNING: item counts differ (scan found {scan_count}, "
            f"query found {query_count}). Investigate before trusting "
            f"the percentage below - results should match exactly."
        )

    improvement_pct = ((scan_avg - query_avg) / scan_avg) * 100

    print("\n--- Summary ---")
    print(f"Matching records ('{TARGET_SEASON}'): {query_count}")
    print(f"scan()+filter average:  {scan_avg:.3f} seconds")
    print(f"query() via GSI average: {query_avg:.3f} seconds")
    print(f"Latency improvement:     {improvement_pct:.1f}%")
    print("\nSave this output. This is your real resume number.")


if __name__ == "__main__":
    main()