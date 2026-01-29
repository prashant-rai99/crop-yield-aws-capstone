from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError

# ===============================
# APP CONFIG
# ===============================

app = Flask(__name__)
app.secret_key = "crop_yield_aws_secret"
REGION = "us-east-1"

# ===============================
# AWS CLIENTS (PRODUCTION SAFE)
# ===============================

try:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
except NoCredentialsError:
    dynamodb = None
    print("❌ AWS credentials not found")

# SNS (optional but enabled)
ENABLE_SNS = True
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:242201289978:Crop_aws"

if ENABLE_SNS:
    try:
        sns = boto3.client("sns", region_name=REGION)
    except Exception as e:
        sns = None
        print("SNS init failed:", e)
else:
    sns = None

# ===============================
# DYNAMODB TABLES (MUST EXIST)
# ===============================

users_table = dynamodb.Table("CropYield_Users")
yield_table = dynamodb.Table("CropYield_Data")

# ===============================
# CONTEXT
# ===============================

@app.context_processor
def inject_now():
    return {"now": datetime.now()}

# ===============================
# SNS HELPER (SAFE)
# ===============================

def send_notification(subject, message):
    if not sns:
        return
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print("SNS error:", e)

# ===============================
# ROUTES
# ===============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/auth/admin")
def auth_admin():
    return render_template("auth_admin.html")

# ===============================
# FARMER SIGNUP
# ===============================

@app.route("/signup/farmer", methods=["POST"])
def signup_farmer():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

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
        flash("Signup successful", "success")
        return redirect(url_for("auth"))

    except Exception as e:
        print("Signup error:", e)
        flash("Signup failed", "error")
        return redirect(url_for("auth"))

# ===============================
# FARMER LOGIN
# ===============================

@app.route("/login/farmer", methods=["POST"])
def login_farmer():
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        res = users_table.get_item(Key={"Email": email})
        if "Item" in res and res["Item"]["Password"] == password:
            session["user"] = email
            session["role"] = "farmer"

            send_notification("Farmer Login", f"{email} logged in")
            return redirect(url_for("dashboard"))

    except Exception as e:
        print("Login error:", e)

    flash("Invalid credentials", "error")
    return redirect(url_for("auth"))

# ===============================
# FARMER DASHBOARD
# ===============================

@app.route("/dashboard")
def dashboard():
    if session.get("role") != "farmer":
        return redirect(url_for("auth"))

    email = session["user"]

    try:
        res = yield_table.query(
            KeyConditionExpression=Key("UserEmail").eq(email)
        )
        yields = res.get("Items", [])
    except Exception as e:
        print("Dashboard error:", e)
        yields = []

    return render_template("dashboard.html", yields=yields)

# ===============================
# ADD YIELD
# ===============================

@app.route("/add-yield", methods=["POST"])
def add_yield():
    if session.get("role") != "farmer":
        return redirect(url_for("auth"))

    try:
        yield_table.put_item(
            Item={
                "UserEmail": session["user"],
                "YieldID": str(uuid.uuid4()),
                "YieldAmount": float(request.form["yield_amount"]),
                "Area": float(request.form["area"]),
                "CreatedAt": datetime.utcnow().isoformat()
            }
        )

        send_notification("Yield Added", f"{session['user']} added yield")
        flash("Yield added successfully", "success")

    except Exception as e:
        print("Add yield error:", e)
        flash("Failed to add yield", "error")

    return redirect(url_for("dashboard"))

# ===============================
# ADMIN
# ===============================

@app.route("/signup/admin", methods=["POST"])
def signup_admin():
    try:
        users_table.put_item(
            Item={
                "Email": request.form["email"],
                "Name": request.form["name"],
                "Password": request.form["password"],
                "Role": "admin",
                "CreatedAt": datetime.utcnow().isoformat()
            }
        )
        flash("Admin registered", "success")
    except Exception as e:
        print("Admin signup error:", e)
        flash("Admin signup failed", "error")

    return redirect(url_for("auth_admin"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("auth_admin"))

    users = users_table.scan().get("Items", [])
    yields = yield_table.scan().get("Items", [])

    return render_template(
        "admin_dashboard.html",
        users=users,
        yields=yields
    )

# ===============================
# LOGOUT
# ===============================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("index"))

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
