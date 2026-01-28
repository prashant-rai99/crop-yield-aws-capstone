import boto3

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url="http://localhost:8000",
    aws_access_key_id="fake",
    aws_secret_access_key="fake"
)

# ---------------- USERS TABLE ----------------
try:
    users_table = dynamodb.create_table(
        TableName="CropYield_Users",
        KeySchema=[
            {"AttributeName": "Email", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "Email", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    users_table.wait_until_exists()
    print("✅ CropYield_Users table created")
except Exception:
    print("ℹ️ CropYield_Users table already exists")

# ---------------- YIELD TABLE ----------------
try:
    yield_table = dynamodb.create_table(
        TableName="CropYield_Data",
        KeySchema=[
            {"AttributeName": "UserEmail", "KeyType": "HASH"},
            {"AttributeName": "YieldID", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "UserEmail", "AttributeType": "S"},
            {"AttributeName": "YieldID", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    yield_table.wait_until_exists()
    print("✅ CropYield_Data table created")
except Exception:
    print("ℹ️ CropYield_Data table already exists")
