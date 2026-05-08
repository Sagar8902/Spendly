import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'expense_tracker.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def register_user(name, email, password):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def get_user_stats(user_id, from_date=None, to_date=None):
    date_filter = "AND date BETWEEN ? AND ?" if (from_date and to_date) else ""
    date_params = (from_date, to_date) if (from_date and to_date) else ()
    conn = get_db()
    try:
        return conn.execute(f"""
            SELECT
                COALESCE(SUM(amount), 0) AS total,
                COUNT(*) AS cnt,
                (SELECT category FROM expenses
                 WHERE user_id = ? {date_filter}
                 GROUP BY category
                 ORDER BY SUM(amount) DESC
                 LIMIT 1) AS top_cat
            FROM expenses
            WHERE user_id = ? {date_filter}
        """, (user_id, *date_params, user_id, *date_params)).fetchone()
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=5, from_date=None, to_date=None):
    if from_date and to_date:
        sql = """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC, id DESC
        """
        params = (user_id, from_date, to_date)
    else:
        sql = """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
        """
        params = (user_id, limit)
    conn = get_db()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_category_breakdown(user_id, from_date=None, to_date=None):
    date_filter = "AND date BETWEEN ? AND ?" if (from_date and to_date) else ""
    date_params = (from_date, to_date) if (from_date and to_date) else ()
    conn = get_db()
    try:
        return conn.execute(f"""
            SELECT
                category AS name,
                SUM(amount) AS total,
                CAST(ROUND(SUM(amount) * 100.0 /
                    (SELECT SUM(amount) FROM expenses WHERE user_id = ? {date_filter}), 0)
                AS INTEGER) AS percent
            FROM expenses
            WHERE user_id = ? {date_filter}
            GROUP BY category
            ORDER BY total DESC
        """, (user_id, *date_params, user_id, *date_params)).fetchall()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] > 0:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    conn.commit()

    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]

    expenses = [
        (user_id, 320.00,  "Food",          "2026-05-01", "Groceries"),
        (user_id, 150.00,  "Transport",     "2026-05-02", "Metro pass top-up"),
        (user_id, 1200.00, "Bills",         "2026-05-03", "Electricity bill"),
        (user_id, 500.00,  "Health",        "2026-05-04", "Pharmacy"),
        (user_id, 250.00,  "Entertainment", "2026-05-05", "Movie tickets"),
        (user_id, 899.00,  "Shopping",      "2026-05-06", "T-shirt"),
        (user_id, 75.00,   "Other",         "2026-05-07", "Stationery"),
        (user_id, 180.00,  "Food",          "2026-05-08", "Restaurant lunch"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
