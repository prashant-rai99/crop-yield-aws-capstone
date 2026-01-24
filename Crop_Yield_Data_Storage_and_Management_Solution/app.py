# Crop Yield Data Storage and Management
# Reference-style Flask App (Non-AWS)

from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ===============================
# In-memory data (temporary)
# ===============================

farmers = {}          # {email: password}
admins = {}           # {email: password}
yield_records = []    # list of dicts

# ===============================
# ROUTES
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
# AUTH – COMMON
# ===============================

@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/auth/admin")
def auth_admin():
    return render_template("auth_admin.html")

# ===============================
# AUTH – FARMER
# ===============================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in farmers:
            return "User already exists!"

        farmers[email] = password
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in farmers and farmers[email] == password:
            session["user"] = email
            session["role"] = "farmer"
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

    user = session["user"]
    my_yields = [y for y in yield_records if y["email"] == user]

    return render_template(
        "dashboard.html",
        user=user,
        yields=my_yields
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

        record = {
            "email": session["user"],
            "crop": crop,
            "season": season,
            "amount": amount,
            "area": area
        }

        yield_records.append(record)
        return redirect(url_for("dashboard"))

    return render_template("add_yield.html")

# ===============================
# ADMIN ROUTES
# ===============================

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in admins:
            return "Admin already exists!"

        admins[email] = password
        return redirect(url_for("admin_login"))

    return render_template("admin_signup.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in admins and admins[email] == password:
            session["admin"] = email
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))

        return "Invalid admin credentials!"

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    return render_template(
        "admin_dashboard.html",
        users=farmers,
        yields=yield_records
    )


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


from datetime import datetime

@app.context_processor
def inject_now():
    return {"now": datetime.now()}

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
