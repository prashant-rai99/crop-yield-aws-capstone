"""
Seed script for generating realistic crop yield records in DynamoDB.

This populates the CropYield_Data and CropYield_Users tables with
realistic, non-trivial data so we can benchmark scan() vs query()
performance at a meaningful scale (Phase 2).

Usage:
    python seed_data.py
"""

import boto3
import uuid
import random
import time
from decimal import Decimal
from datetime import datetime, timedelta

REGION = "us-east-1"
NUM_FARMERS = 200
RECORDS_PER_FARMER_MIN = 40
RECORDS_PER_FARMER_MAX = 60
TOTAL_TARGET_RECORDS = 10000

dynamodb = boto3.resource("dynamodb", region_name=REGION)
users_table = dynamodb.Table("CropYield_Users")
yield_table = dynamodb.Table("CropYield_Data")

CROPS = [
    "Rice", "Wheat", "Maize", "Sugarcane", "Cotton",
    "Soybean", "Groundnut", "Mustard", "Barley", "Bajra",
    "Jowar", "Gram", "Potato", "Onion", "Tomato"
]

SEASONS = ["Kharif", "Rabi", "Zaid"]

FIRST_NAMES = [
    "Ravi", "Suresh", "Anita", "Priya", "Manoj", "Sunita", "Rajesh",
    "Kavita", "Vijay", "Deepak", "Sanjay", "Meena", "Arun", "Pooja",
    "Ramesh", "Geeta", "Ashok", "Nisha", "Vikram", "Rekha"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Singh", "Patel", "Yadav", "Verma", "Gupta",
    "Reddy", "Rao", "Mishra", "Chauhan", "Joshi", "Nair", "Das"
]


def random_date_within_last_years(years=3):
    days_back = random.randint(0, 365 * years)
    return (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")


def generate_farmer_email(index):
    return f"seed_farmer_{index}@example.com"


def create_farmer(index):
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    email = generate_farmer_email(index)

    users_table.put_item(
        Item={
            "Email": email,
            "Name": name,
            "Password": "seed-data-not-a-real-login",
            "Role": "farmer",
            "CreatedAt": datetime.utcnow().isoformat()
        }
    )
    return email


def create_yield_record(email):
    crop = random.choice(CROPS)
    season = random.choice(SEASONS)
    area = round(random.uniform(0.5, 20.0), 2)
    yield_rate = round(random.uniform(1.5, 6.0), 2)
    yield_amount = round(area * yield_rate, 2)

    yield_table.put_item(
        Item={
            "UserEmail": email,
            "YieldID": str(uuid.uuid4()),
            "crop_name": crop,
            "season": season,
            "YieldAmount": Decimal(str(yield_amount)),
            "Area": Decimal(str(area)),
            "CreatedAt": random_date_within_last_years()
        }
    )


def main():
    print(f"Seeding {NUM_FARMERS} farmers and up to {TOTAL_TARGET_RECORDS} yield records...")
    start_time = time.time()

    total_records = 0
    for i in range(NUM_FARMERS):
        email = create_farmer(i)

        records_for_this_farmer = random.randint(
            RECORDS_PER_FARMER_MIN, RECORDS_PER_FARMER_MAX
        )

        for _ in range(records_for_this_farmer):
            if total_records >= TOTAL_TARGET_RECORDS:
                break
            create_yield_record(email)
            total_records += 1

        if (i + 1) % 20 == 0:
            elapsed = time.time() - start_time
            print(f"  {i + 1}/{NUM_FARMERS} farmers done, {total_records} records so far ({elapsed:.1f}s elapsed)")

        if total_records >= TOTAL_TARGET_RECORDS:
            break

    elapsed = time.time() - start_time
    print(f"\nDone. Seeded {total_records} yield records across {i + 1} farmers in {elapsed:.1f} seconds.")


if __name__ == "__main__":
    main()