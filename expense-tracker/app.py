import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, register_user, get_user_by_email

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-change-in-prod')

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name:
            return render_template("register.html", error="Name is required.", name=name, email=email)
        if "@" not in email:
            return render_template("register.html", error="Enter a valid email address.", name=name, email=email)
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)

        try:
            register_user(name, email, password)
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.", email=email)

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("landing"))

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile_page():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "member_since": "January 2026",
    }
    stats = {
        "total_spent": "₹3,574",
        "transaction_count": 8,
        "top_category": "Bills",
    }
    transactions = [
        {"date": "08 May 2026", "description": "Restaurant lunch",  "category": "Food",          "amount": "₹180.00"},
        {"date": "07 May 2026", "description": "Stationery",        "category": "Other",         "amount": "₹75.00"},
        {"date": "06 May 2026", "description": "T-shirt",           "category": "Shopping",      "amount": "₹899.00"},
        {"date": "05 May 2026", "description": "Movie tickets",     "category": "Entertainment", "amount": "₹250.00"},
        {"date": "04 May 2026", "description": "Pharmacy",          "category": "Health",        "amount": "₹500.00"},
    ]
    categories = [
        {"name": "Bills",         "amount": "₹1,200", "percent": 34},
        {"name": "Shopping",      "amount": "₹899",   "percent": 25},
        {"name": "Health",        "amount": "₹500",   "percent": 14},
        {"name": "Food",          "amount": "₹500",   "percent": 14},
        {"name": "Entertainment", "amount": "₹250",   "percent": 7},
        {"name": "Transport",     "amount": "₹150",   "percent": 4},
        {"name": "Other",         "amount": "₹75",    "percent": 2},
    ]
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
