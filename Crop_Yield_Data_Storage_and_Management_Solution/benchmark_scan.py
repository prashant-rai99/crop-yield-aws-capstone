"""
Benchmark script for measuring DynamoDB scan() latency on CropYield_Data.

This simulates what the current admin dashboard does (a full table scan)
and measures how long it takes, so we have a real baseline number before
introducing a Global Secondary Index and query() in the next step.

Usage:
    python benchmark_scan.py
"""

import boto3
import time
import statistics

REGION = "us-east-1"
NUM_RUNS = 5

dynamodb = boto3.resource("dynamodb", region_name=REGION)
yield_table = dynamodb.Table("CropYield_Data")


def run_full_scan():
    start = time.perf_counter()

    items = []
    response = yield_table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = yield_table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    elapsed = time.perf_counter() - start
    return elapsed, len(items)


def main():
    print(f"Running {NUM_RUNS} scan() passes over CropYield_Data...\n")

    timings = []
    record_count = 0

    for run_number in range(1, NUM_RUNS + 1):
        elapsed, count = run_full_scan()
        record_count = count
        timings.append(elapsed)
        print(f"  Run {run_number}: {elapsed:.3f} seconds ({count} items)")

    avg_time = statistics.mean(timings)
    min_time = min(timings)
    max_time = max(timings)

    print("\n--- scan() Benchmark Summary ---")
    print(f"Records scanned: {record_count}")
    print(f"Average time:    {avg_time:.3f} seconds")
    print(f"Min time:        {min_time:.3f} seconds")
    print(f"Max time:        {max_time:.3f} seconds")
    print("\nSave these numbers. We'll compare against query() next.")


if __name__ == "__main__":
    main()