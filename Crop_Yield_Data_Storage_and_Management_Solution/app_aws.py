# Crop Yield Data Storage and Management
# AWS Integrated Flask App (HTML + Reference Aligned)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = "crop_yield_aws_secret"

# ===============================
# AWS CONFIGURATION
# ===============================

REGION = "us-east-1"

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url="http://localhost:8000",
    aws_access_key_id="fake",
    aws_secret_access_key="fake"
)

sns = None  # Local testing ke liye SNS off

# DynamoDB Tables (MUST exist)
users_table = dynamodb.Table("CropYield_Users")
yield_table = dynamodb.Table("CropYield_Data")

# 🔴 Replace with YOUR real SNS ARN
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:242201289978:Crop_aws:e90b5c81-2568-4276-84a4-460803fdb72a"

# ===============================
# CONTEXT PROCESSOR
# ===============================

@app.context_processor
def inject_now():
    return {"now": datetime.now()}

# ===============================
# SNS HELPER
# ===============================

def send_notification(subject, message):
    if sns is None:
        print(f"[SNS MOCK] {subject}: {message}")
        return

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
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")

# ===============================
# AUTH PAGES
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

@app.route("/signup/farmer", methods=["POST"])
def signup_farmer():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    try:
        res = users_table.get_item(Key={"Email": email})
        if "Item" in res:
            flash("Farmer already exists", "error")
            return redirect(url_for("auth"))

        users_table.put_item(
            Item={
                "Email": email,
                "Name": name,
                "Password": password,
                "Role": "farmer",
                "CreatedAt": datetime.utcnow().isoformat()
            }
        )

        send_notification("New Farmer Signup", f"{email} registered")

        flash("Farmer registered successfully", "success")
        return redirect(url_for("auth"))

    except ClientError as e:
        print(e)
        flash("Signup failed", "error")
        return redirect(url_for("auth"))


@app.route("/login/farmer", methods=["POST"])
def login_farmer():
    email = request.form["email"]
    password = request.form["password"]

    res = users_table.get_item(Key={"Email": email})

    if "Item" in res and res["Item"]["Password"] == password and res["Item"]["Role"] == "farmer":
        session["user"] = email
        session["name"] = res["Item"]["Name"]
        session["role"] = "farmer"

        send_notification("Farmer Login", f"{email} logged in")

        flash("Login successful", "success")
        return redirect(url_for("dashboard"))

    flash("Invalid farmer credentials", "error")
    return redirect(url_for("auth"))

# ===============================
# FARMER DASHBOARD
# ===============================

@app.route("/dashboard")
def dashboard():
    if "user" not in session or session.get("role") != "farmer":
        return redirect(url_for("auth"))

    email = session["user"]

    res = yield_table.query(
        KeyConditionExpression=Key("UserEmail").eq(email)
    )

    yields = res.get("Items", [])

    stats = {
        "total_records": len(yields),
        "total_area": sum(float(y["Area"]) for y in yields) if yields else 0,
        "total_production": sum(float(y["YieldAmount"]) for y in yields) if yields else 0,
        "avg_yield": round(
            (sum(float(y["YieldAmount"]) for y in yields) /
             sum(float(y["Area"]) for y in yields)), 2
        ) if yields else 0
    }

    return render_template(
        "dashboard.html",
        yields=yields,
        stats=stats
    )


@app.route("/add-yield", methods=["GET", "POST"])
def add_yield():
    if "user" not in session or session.get("role") != "farmer":
        return redirect(url_for("auth"))

    if request.method == "POST":
        yield_table.put_item(
            Item={
                "UserEmail": session["user"],
                "YieldID": str(uuid.uuid4()),
                "crop_name": request.form["crop_name"],
                "season": request.form["season"],
                "YieldAmount": float(request.form["yield_amount"]),
                "Area": float(request.form["area"]),
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d")
            }
        )

        send_notification(
            "Yield Added",
            f"{session['user']} added yield data"
        )

        flash("Yield record added", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_yield.html")

# ===============================
# ADMIN AUTH
# ===============================

@app.route("/signup/admin", methods=["POST"])
def signup_admin():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    res = users_table.get_item(Key={"Email": email})
    if "Item" in res:
        flash("Admin already exists", "error")
        return redirect(url_for("auth_admin"))

    users_table.put_item(
        Item={
            "Email": email,
            "Name": name,
            "Password": password,
            "Role": "admin",
            "CreatedAt": datetime.utcnow().isoformat()
        }
    )

    flash("Admin registered successfully", "success")
    return redirect(url_for("auth_admin"))


@app.route("/login/admin", methods=["POST"])
def login_admin():
    email = request.form["email"]
    password = request.form["password"]

    res = users_table.get_item(Key={"Email": email})

    if (
        "Item" in res
        and res["Item"]["Password"] == password
        and res["Item"]["Role"] == "admin"
    ):
        session["user"] = email
        session["name"] = res["Item"]["Name"]
        session["role"] = "admin"

        flash("Admin login successful", "success")
        return redirect(url_for("admin_dashboard"))

    flash("Invalid admin credentials", "error")
    return redirect(url_for("auth_admin"))

# ===============================
# ADMIN DASHBOARD
# ===============================

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("auth_admin"))

    users = users_table.scan().get("Items", [])
    yields = yield_table.scan().get("Items", [])

    stats = {
        "total_users": len(users),
        "total_farmers": len([u for u in users if u["Role"] == "farmer"]),
        "total_admins": len([u for u in users if u["Role"] == "admin"]),
        "total_records": len(yields),
        "total_production": sum(float(y["YieldAmount"]) for y in yields) if yields else 0
    }

    return render_template(
        "admin_dashboard.html",
        users=users,
        yields=yields,
        stats=stats
    )

# ===============================
# LOGOUT
# ===============================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))

# ===============================
# RUN (EC2)
# ===============================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
