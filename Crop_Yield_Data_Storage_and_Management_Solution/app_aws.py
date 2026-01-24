# Crop Yield Data Storage and Management
# AWS Integrated Flask App (Reference Style)

from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ===============================
# AWS CONFIGURATION
# ===============================

REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# DynamoDB Tables (MUST exist)
users_table = dynamodb.Table("CropYield_Users")
yield_table = dynamodb.Table("CropYield_Data")

# ⚠️ Replace with your REAL SNS ARN
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:CropYieldAlerts"

# ===============================
# CONTEXT PROCESSOR (for {{ now.year }})
# ===============================

@app.context_processor
def inject_now():
    return {"now": datetime.now()}

# ===============================
# SNS HELPER
# ===============================

def send_notification(subject, message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print("SNS Error:", e)

# ===============================
# PUBLIC ROUTES
# ===============================

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")

# ===============================
# AUTH COMMON (TEMPLATE COMPATIBLE)
# ===============================

@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/auth/admin")
def auth_admin():
    return render_template("auth_admin.html")

# ===============================
# FARMER AUTH
# ===============================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        res = users_table.get_item(Key={"Email": email})
        if "Item" in res:
            return "User already exists!"

        users_table.put_item(
            Item={
                "Email": email,
                "Password": password,
                "Role": "farmer",
                "CreatedAt": datetime.utcnow().isoformat()
            }
        )

        send_notification(
            "New Farmer Signup",
            f"Farmer {email} registered"
        )

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        res = users_table.get_item(Key={"Email": email})
        if "Item" in res and res["Item"]["Password"] == password:
            session["user"] = email
            session["role"] = "farmer"

            send_notification(
                "Farmer Login",
                f"{email} logged in"
            )

            return redirect(url_for("dashboard"))

        return "Invalid credentials!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ===============================
# FARMER DASHBOARD
# ===============================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]

    res = yield_table.query(
        KeyConditionExpression=Key("UserEmail").eq(email)
    )

    yields = res.get("Items", [])

    return render_template(
        "dashboard.html",
        user=email,
        yields=yields
    )


@app.route("/add-yield", methods=["GET", "POST"])
def add_yield():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        crop = request.form["crop"]
        season = request.form["season"]
        amount = request.form["amount"]
        area = request.form["area"]

        yield_table.put_item(
            Item={
                "UserEmail": session["user"],
                "Timestamp": datetime.utcnow().isoformat(),
                "YieldID": str(uuid.uuid4()),
                "Crop": crop,
                "Season": season,
                "YieldAmount": amount,
                "Area": area
            }
        )

        send_notification(
            "Yield Added",
            f"{session['user']} added yield for {crop}"
        )

        return redirect(url_for("dashboard"))

    return render_template("add_yield.html")

# ===============================
# ADMIN ROUTES
# ===============================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        res = users_table.get_item(Key={"Email": email})
        if (
            "Item" in res
            and res["Item"]["Password"] == password
            and res["Item"]["Role"] == "admin"
        ):
            session["admin"] = email
            return redirect(url_for("admin_dashboard"))

        return "Invalid admin credentials!"

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    users = users_table.scan().get("Items", [])
    yields = yield_table.scan().get("Items", [])

    return render_template(
        "admin_dashboard.html",
        users=users,
        yields=yields
    )


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
