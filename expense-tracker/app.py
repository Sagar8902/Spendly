import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import check_password_hash
from database.db import (get_db, init_db, seed_db, register_user, get_user_by_email,
                         get_user_by_id, get_user_stats, get_recent_transactions,
                         get_category_breakdown)

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

    user_id = session["user_id"]
    row = get_user_by_id(user_id)
    if row is None:
        abort(404)

    member_since = datetime.strptime(
        row["created_at"], "%Y-%m-%d %H:%M:%S"
    ).strftime("%B %Y")

    user = {
        "name":         row["name"],
        "email":        row["email"],
        "member_since": member_since,
    }

    s = get_user_stats(user_id)
    stats = {
        "total_spent":       f"₹{s['total']:,.0f}",
        "transaction_count": s["cnt"],
        "top_category":      s["top_cat"] or "—",
    }

    transactions = [
        {
            "date":        datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%d %b %Y"),
            "description": tx["description"],
            "category":    tx["category"],
            "amount":      f"₹{tx['amount']:.2f}",
        }
        for tx in get_recent_transactions(user_id)
    ]

    categories = [
        {
            "name":    cat["name"],
            "amount":  f"₹{cat['total']:,.0f}",
            "percent": cat["percent"],
        }
        for cat in get_category_breakdown(user_id)
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
