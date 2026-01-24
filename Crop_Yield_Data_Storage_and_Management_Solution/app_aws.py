"""
AWS Service Layer for Crop Yield Data Storage and Management
"""

import os
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

# ================= AWS CONFIG =================

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")

DYNAMODB_USER_TABLE = os.environ.get(
    "DYNAMODB_USER_TABLE", "CropYield_Users"
)
DYNAMODB_YIELD_TABLE = os.environ.get(
    "DYNAMODB_YIELD_TABLE", "CropYield_Data"
)

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

# ================= AWS CLIENTS =================

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sns_client = boto3.client("sns", region_name=AWS_REGION)

user_table = dynamodb.Table(DYNAMODB_USER_TABLE)
yield_table = dynamodb.Table(DYNAMODB_YIELD_TABLE)

# ================= USER FUNCTIONS =================

def create_user(email, password, name, role="farmer"):
    try:
        res = user_table.get_item(Key={"Email": email})
        if "Item" in res:
            return False, "User already exists"

        user_table.put_item(
            Item={
                "Email": email,
                "Password": password,  # hash later
                "Name": name,
                "Role": role,
                "CreatedAt": datetime.utcnow().isoformat()
            }
        )
        return True, "User created"

    except ClientError as e:
        return False, str(e)


def verify_user(email, password):
    try:
        res = user_table.get_item(Key={"Email": email})
        if "Item" not in res:
            return False, None

        user = res["Item"]
        if user["Password"] == password:
            return True, user

        return False, None

    except ClientError:
        return False, None


def get_all_users():
    try:
        res = user_table.scan()
        return res.get("Items", [])
    except ClientError:
        return []


# ================= YIELD FUNCTIONS =================

def add_yield_data(email, crop_name, season, yield_amount, area):
    try:
        item = {
            "UserEmail": email,
            "Timestamp": datetime.utcnow().isoformat(),
            "YieldID": str(uuid.uuid4()),
            "CropName": crop_name,
            "Season": season,
            "YieldAmount": float(yield_amount),
            "Area": float(area)
        }
        yield_table.put_item(Item=item)
        return True, item

    except ClientError as e:
        return False, str(e)


def get_user_yields(email):
    try:
        res = yield_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("UserEmail").eq(email)
        )
        return res.get("Items", [])
    except ClientError:
        return []


def get_all_yields():
    try:
        res = yield_table.scan()
        return res.get("Items", [])
    except ClientError:
        return []


# ================= SNS =================

def send_sns_notification(message, subject="Crop Yield Alert"):
    if not SNS_TOPIC_ARN:
        return False

    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        return True
    except ClientError:
        return False
