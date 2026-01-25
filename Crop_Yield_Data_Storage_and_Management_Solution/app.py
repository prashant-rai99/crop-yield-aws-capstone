# Crop Yield Data Storage and Management
# Reference-style Flask App (Non-AWS, HTML-aligned)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "crop_yield_secret_key"

# ===============================
# In-memory data (temporary)
# ===============================

farmers = {}          # email -> {name, password}
admins = {}           # email -> {name, password}
yield_records = []    # list of dicts

# ===============================
# BASIC ROUTES
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

    if email in farmers:
        flash("Farmer already exists", "error")
        return redirect(url_for("auth"))

    farmers[email] = {
        "name": name,
        "password": password
    }

    flash("Farmer registered successfully", "success")
    return redirect(url_for("auth"))


@app.route("/login/farmer", methods=["POST"])
def login_farmer():
    email = request.form["email"]
    password = request.form["password"]

    if email in farmers and farmers[email]["password"] == password:
        session["user"] = email
        session["name"] = farmers[email]["name"]
        session["role"] = "farmer"

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

    user_email = session["user"]
    user_yields = [y for y in yield_records if y["email"] == user_email]

    stats = {
        "total_records": len(user_yields),
        "total_area": sum(float(y["area"]) for y in user_yields) if user_yields else 0,
        "total_production": sum(float(y["yield_amount"]) for y in user_yields) if user_yields else 0,
        "avg_yield": round(
            (sum(float(y["yield_amount"]) for y in user_yields) /
             sum(float(y["area"]) for y in user_yields)), 2
        ) if user_yields else 0
    }

    return render_template(
        "dashboard.html",
        yields=user_yields,
        stats=stats
    )


@app.route("/add-yield", methods=["GET", "POST"])
def add_yield():
    if "user" not in session or session.get("role") != "farmer":
        return redirect(url_for("auth"))

    if request.method == "POST":
        record = {
            "id": len(yield_records) + 1,
            "email": session["user"],
            "user_name": session["name"],
            "crop_name": request.form["crop_name"],
            "season": request.form["season"],
            "yield_amount": float(request.form["yield_amount"]),
            "area": float(request.form["area"]),
            "timestamp": datetime.now().strftime("%Y-%m-%d")
        }

        yield_records.append(record)
        flash("Yield record added successfully", "success")
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

    if email in admins:
        flash("Admin already exists", "error")
        return redirect(url_for("auth_admin"))

    admins[email] = {
        "name": name,
        "password": password
    }

    flash("Admin registered successfully", "success")
    return redirect(url_for("auth_admin"))


@app.route("/login/admin", methods=["POST"])
def login_admin():
    email = request.form["email"]
    password = request.form["password"]

    if email in admins and admins[email]["password"] == password:
        session["user"] = email
        session["name"] = admins[email]["name"]
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

    stats = {
        "total_users": len(farmers) + len(admins),
        "total_farmers": len(farmers),
        "total_admins": len(admins),
        "total_records": len(yield_records),
        "total_production": sum(float(y["yield_amount"]) for y in yield_records) if yield_records else 0
    }

    return render_template(
        "admin_dashboard.html",
        users=[
            {"name": v["name"], "email": k, "role": "Farmer"}
            for k, v in farmers.items()
        ] + [
            {"name": v["name"], "email": k, "role": "Admin"}
            for k, v in admins.items()
        ],
        yields=yield_records,
        stats=stats
    )


# ===============================
# LOGOUT (COMMON)
# ===============================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))


# ===============================
# CONTEXT PROCESSOR
# ===============================

@app.context_processor
def inject_now():
    return {"now": datetime.now()}


# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(debug=True)
