from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
import os
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from botocore.exceptions import NoCredentialsError
from werkzeug.security import generate_password_hash, check_password_hash

# ===============================
# APP CONFIG
# ===============================

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-fallback-key")
REGION = "us-east-1"

# ===============================
# AWS CLIENTS
# ===============================

try:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
except NoCredentialsError:
    dynamodb = None
    print("AWS credentials not found")

# SNS
ENABLE_SNS = True
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

sns = None
if ENABLE_SNS:
    try:
        sns = boto3.client("sns", region_name=REGION)
    except Exception as e:
        print("SNS init failed:", e)

# ===============================
# TABLES
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
# SNS HELPER
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
# PUBLIC ROUTES
# ===============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

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
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    res = users_table.get_item(Key={"Email": email})
    if "Item" in res:
        flash("Farmer already exists", "error")
        return redirect(url_for("auth"))

    users_table.put_item(
        Item={
            "Email": email,
            "Name": name,
            "Password": generate_password_hash(password),
            "Role": "farmer",
            "CreatedAt": datetime.utcnow().isoformat()
        }
    )

    send_notification("New Farmer Signup", f"{email} registered")
    flash("Signup successful", "success")
    return redirect(url_for("auth"))

# ===============================
# FARMER LOGIN
# ===============================

@app.route("/login/farmer", methods=["POST"])
def login_farmer():
    session.clear()   

    email = request.form["email"]
    password = request.form["password"]

    res = users_table.get_item(Key={"Email": email})

    if "Item" in res and check_password_hash(res["Item"]["Password"], password):
        session["user"] = email
        session["name"] = res["Item"]["Name"]
        session["role"] = "farmer"

        send_notification("Farmer Login", f"{email} logged in")
        return redirect(url_for("dashboard"))

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

    res = yield_table.query(
        KeyConditionExpression=Key("UserEmail").eq(email)
    )
    yields = res.get("Items", [])

    total_area = sum(float(y.get("Area", 0)) for y in yields)
    total_production = sum(float(y.get("YieldAmount", 0)) for y in yields)

    stats = {
        "total_records": len(yields),
        "total_area": total_area,
        "total_production": total_production,
        "avg_yield": round(total_production / total_area, 2) if total_area > 0 else 0
    }

    return render_template(
        "dashboard.html",
        yields=yields,
        stats=stats,
        farmer_name=session.get("name")
    )

# ===============================
# ADD YIELD (GET + POST)
# ===============================

@app.route("/add-yield", methods=["GET", "POST"])
def add_yield():
    if session.get("role") != "farmer":
        return redirect(url_for("auth"))

    if request.method == "POST":
        try:
            yield_table.put_item(
                Item={
                    "UserEmail": session["user"],
                    "YieldID": str(uuid.uuid4()),
                    "YieldAmount": Decimal(request.form["yield_amount"]),  
                    "Area": Decimal(request.form["area"]),                
                    "CreatedAt": datetime.utcnow().strftime("%Y-%m-%d")
                }
            )

            send_notification("Yield Added", f"{session['user']} added yield")
            flash("Yield added successfully", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            print("Add yield error:", e)
            flash("Failed to add yield", "error")
            return redirect(url_for("dashboard"))

    return render_template("add_yield.html")

# ===============================
# ADMIN SIGNUP
# ===============================

@app.route("/signup/admin", methods=["POST"])
def signup_admin():
    users_table.put_item(
        Item={
            "Email": request.form["email"],
            "Name": request.form["name"],
            "Password": generate_password_hash(request.form["password"]),
            "Role": "admin",
            "CreatedAt": datetime.utcnow().isoformat()
        }
    )

    flash("Admin registered successfully", "success")
    return redirect(url_for("auth_admin"))

# ===============================
# ADMIN LOGIN
# ===============================

@app.route("/login/admin", methods=["POST"]) 
def login_admin():
    session.clear()   

    email = request.form["email"]
    password = request.form["password"]

    res = users_table.get_item(Key={"Email": email})

    if (
        "Item" in res
        and check_password_hash(res["Item"]["Password"], password)
        and res["Item"]["Role"] == "admin"
    ):
        session["user"] = email
        session["name"] = res["Item"]["Name"]
        session["role"] = "admin"
        return redirect(url_for("admin_dashboard"))

    flash("Invalid admin credentials", "error")
    return redirect(url_for("auth_admin"))

# ===============================
# ADMIN DASHBOARD
# ===============================

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("auth_admin"))

    users = users_table.scan().get("Items", [])
    yields = yield_table.scan().get("Items", [])

    stats = {
        "total_users": len(users),
        "total_farmers": len([u for u in users if u["Role"] == "farmer"]),
        "total_yields": len(yields)
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
# RUN
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)