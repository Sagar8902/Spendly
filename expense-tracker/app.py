import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for
from database.db import get_db, init_db, seed_db, register_user

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


@app.route("/login")
def login():
    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
