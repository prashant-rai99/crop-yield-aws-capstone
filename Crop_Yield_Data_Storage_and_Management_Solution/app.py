"""
Crop Yield Data Storage and Management Solution
Cloud-ready Flask application with AWS integration
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime
import os

# 🔗 AWS Service Layer
from app_aws import (
    create_user,
    verify_user,
    add_yield_data,
    get_user_yields,
    get_all_users,
    get_all_yields,
    send_sns_notification
)

# =============================================================================
# FLASK APP SETUP
# =============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# =============================================================================
# DECORATORS
# =============================================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session or session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("auth_admin"))
        return f(*args, **kwargs)
    return decorated

# =============================================================================
# PUBLIC ROUTES
# =============================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")

# =============================================================================
# AUTH ROUTES
# =============================================================================

@app.route("/auth")
def auth():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("auth.html")


@app.route("/auth/admin")
def auth_admin():
    if "user" in session and session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return render_template("auth_admin.html")

# =============================================================================
# SIGNUP
# =============================================================================

@app.route("/signup/farmer", methods=["POST"])
def signup_farmer():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not all([name, email, password]):
        flash("All fields are required.", "error")
        return redirect(url_for("auth"))

    success, message = create_user(email, password, name, role="farmer")
    if not success:
        flash(message, "error")
        return redirect(url_for("auth"))

    send_sns_notification(f"New farmer registered: {email}")
    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("auth"))


@app.route("/signup/admin", methods=["POST"])
def signup_admin():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not all([name, email, password]):
        flash("All fields are required.", "error")
        return redirect(url_for("auth_admin"))

    success, message = create_user(email, password, name, role="admin")
    if not success:
        flash(message, "error")
        return redirect(url_for("auth_admin"))

    flash("Admin account created. Please log in.", "success")
    return redirect(url_for("auth_admin"))

# =============================================================================
# LOGIN
# =============================================================================

@app.route("/login/farmer", methods=["POST"])
def login_farmer():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    success, user = verify_user(email, password)
    if not success or user.get("Role") != "farmer":
        flash("Invalid farmer credentials.", "error")
        return redirect(url_for("auth"))

    session["user"] = user["Email"]
    session["name"] = user["Name"]
    session["role"] = "farmer"
    flash(f"Welcome, {user['Name']}!", "success")
    return redirect(url_for("dashboard"))


@app.route("/login/admin", methods=["POST"])
def login_admin():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    success, user = verify_user(email, password)
    if not success or user.get("Role") != "admin":
        flash("Invalid admin credentials.", "error")
        return redirect(url_for("auth_admin"))

    session["user"] = user["Email"]
    session["name"] = user["Name"]
    session["role"] = "admin"
    flash("Admin login successful.", "success")
    return redirect(url_for("admin_dashboard"))

# =============================================================================
# LOGOUT
# =============================================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

# =============================================================================
# FARMER DASHBOARD
# =============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    email = session["user"]
    yields = get_user_yields(email)

    return render_template("dashboard.html", yields=yields)

@app.route("/add_yield", methods=["GET", "POST"])
@login_required
def add_yield():
    if request.method == "POST":
        crop = request.form.get("crop_name")
        season = request.form.get("season")
        amount = request.form.get("yield_amount")
        area = request.form.get("area")

        success, _ = add_yield_data(
            session["user"], crop, season, amount, area
        )

        if success:
            send_sns_notification(
                f"{session['user']} added yield data for {crop}"
            )
            flash("Yield data added successfully.", "success")
            return redirect(url_for("dashboard"))

        flash("Failed to add yield data.", "error")

    return render_template("add_yield.html")

# =============================================================================
# ADMIN DASHBOARD
# =============================================================================

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    users = get_all_users()
    yields = get_all_yields()
    return render_template(
        "admin_dashboard.html",
        users=users,
        yields=yields
    )

# =============================================================================
# CONTEXT
# =============================================================================

@app.context_processor
def inject_now():
    return {"now": datetime.now()}

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
