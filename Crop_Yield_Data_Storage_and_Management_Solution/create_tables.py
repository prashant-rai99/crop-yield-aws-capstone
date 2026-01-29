import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"

# DynamoDB resource (IAM role / credentials required)
dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION
)

# ===============================
# USERS TABLE
# ===============================
try:
    users_table = dynamodb.create_table(
        TableName="CropYield_Users",
        KeySchema=[
            {"AttributeName": "Email", "KeyType": "HASH"}  # Partition Key
        ],
        AttributeDefinitions=[
            {"AttributeName": "Email", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    users_table.wait_until_exists()
    print("✅ CropYield_Users table created")

except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print("ℹ️ CropYield_Users table already exists")
    else:
        print("❌ Error creating CropYield_Users:", e)

# ===============================
# YIELD DATA TABLE
# ===============================
try:
    yield_table = dynamodb.create_table(
        TableName="CropYield_Data",
        KeySchema=[
            {"AttributeName": "UserEmail", "KeyType": "HASH"},   # Partition Key
            {"AttributeName": "YieldID", "KeyType": "RANGE"}    # Sort Key
        ],
        AttributeDefinitions=[
            {"AttributeName": "UserEmail", "AttributeType": "S"},
            {"AttributeName": "YieldID", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    yield_table.wait_until_exists()
    print("✅ CropYield_Data table created")

except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceInUseException":
        print("ℹ️ CropYield_Data table already exists")
    else:
        print("❌ Error creating CropYield_Data:", e)

print("🎯 DynamoDB setup complete")
