"""
Export DynamoDB yield data to S3 as JSON Lines, partitioned by season.

This script scans the CropYield_Data DynamoDB table, converts each item
into a JSON-serializable dict, groups items by season, writes one
JSON Lines file per season locally, then uploads each file to S3 under
a season=<value> "folder" prefix. This partition-by-season layout lets
Athena skip irrelevant partitions when a query filters on season,
which keeps query cost and latency down.

Usage:
    python export_to_s3.py

Requires AWS credentials configured locally (same crop-yield-admin
credentials already used for seed_data.py / benchmark scripts).
"""

import json
import os
from collections import defaultdict
from decimal import Decimal

import boto3

# --- Configuration ---
AWS_REGION = "us-east-1"
DYNAMODB_TABLE_NAME = "CropYield_Data"
S3_BUCKET_NAME = "crop-yield-datalake-982515248045"
S3_PREFIX = "yield-data"  # top-level folder inside the bucket
LOCAL_EXPORT_DIR = "export_temp"


def decimal_to_native(obj):
    """Convert DynamoDB Decimal values into plain int/float so json.dumps works."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def scan_all_items(table):
    """Scan the full table, handling pagination since scan() caps at 1MB per page."""
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


def group_by_season(items):
    """Group items into a dict keyed by season value, defaulting unknowns to 'Unknown'."""
    grouped = defaultdict(list)
    for item in items:
        season = item.get("season", "Unknown")
        grouped[season].append(item)
    return grouped


def write_and_upload(grouped_items, s3_client):
    os.makedirs(LOCAL_EXPORT_DIR, exist_ok=True)

    for season, items in grouped_items.items():
        local_filename = os.path.join(LOCAL_EXPORT_DIR, f"{season}.jsonl")

        with open(local_filename, "w") as f:
            for item in items:
                f.write(json.dumps(item, default=decimal_to_native) + "\n")

        s3_key = f"{S3_PREFIX}/season={season}/data.jsonl"
        s3_client.upload_file(local_filename, S3_BUCKET_NAME, s3_key)

        print(f"  season={season}: {len(items)} records -> s3://{S3_BUCKET_NAME}/{s3_key}")


def main():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    print(f"Scanning table '{DYNAMODB_TABLE_NAME}'...")
    items = scan_all_items(table)
    print(f"Total records fetched: {len(items)}")

    grouped_items = group_by_season(items)
    print(f"Seasons found: {list(grouped_items.keys())}")

    print("Writing local files and uploading to S3...")
    write_and_upload(grouped_items, s3_client)

    print("\nExport complete.")


if __name__ == "__main__":
    main()