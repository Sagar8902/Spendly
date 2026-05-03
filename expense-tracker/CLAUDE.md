# CLAUDE.md

## Project Overview

**Spendly** is a Flask-based personal expense tracker targeting Indian users (currency in ₹).  
This is a guided learning project built incrementally — `expense-tracker/file.txt` contains the step-by-step task list tracking what has been built and what comes next.

---

## Architecture

All application code lives under `expense-tracker/`.

expense-tracker/
├── app.py              # All routes — single file, no blueprints
├── database/
│   └── db.py           # SQLite helpers: get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this
│   └── *.html          # One template per page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles (~835 lines) — do not split
│   │   └── landing.css     # Landing-page-only styles
│   └── js/
│       └── main.js         # Vanilla JS only
├── .env                    # Gitignored — holds SECRET_KEY and config
└── requirements.txt


**Where things belong:**
- New routes → `app.py` only, no blueprints
- DB logic → `database/db.py` only, never inline in routes
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags

---

## Code Style

- Python: PEP 8, `snake_case` for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- DB queries: always use parameterized queries (`?` placeholders) — never f-strings in SQL
- Error handling: use `abort()` for HTTP errors, not bare `return "error string"`
- Python 3.10+ assumed — f-strings and `match` statements are fine

---

## Tech Constraints

- **Flask only** — no FastAPI, no Django, no other web frameworks
- **SQLite only** — no PostgreSQL, no SQLAlchemy ORM; raw SQL via `sqlite3` stdlib
- **Vanilla JS only** — no React, no jQuery, no npm packages
- **No new pip packages** — work within `requirements.txt` as-is unless explicitly told otherwise
- Flask debug mode is on (`debug=True`) in `app.py`; port is **5001**

---

## Design System

Defined in `static/css/style.css` at `:root`:

| Token | Value | Usage |
|---|---|---|
| Background | `#f7f6f3` | Light paper |
| Text | `#0f0f0f` | Dark ink |
| Primary | `#1a472a` | Forest green — main actions |
| Secondary | `#c17f24` | Warm gold — accents |
| Danger | `#c0392b` | Destructive actions |

**Typography:** DM Serif Display (headings) + DM Sans (body) — loaded from Google Fonts in `base.html`.  
**Responsive breakpoints:** 600px and 900px.

---

## Database Module (`database/db.py`)

Currently empty — helpers are implemented step-by-step. Expected exports when complete:

- `get_db()` — returns a connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`
- `init_db()` — runs `CREATE TABLE IF NOT EXISTS` for all tables
- `seed_db()` — inserts sample data for development

The DB file `expense_tracker.db` is gitignored.

> **Do not assume any helper exists until the step that implements it.**

---

## Subagent Policy

- Always use a built-in **explore subagent** for codebase exploration before implementing any new feature
- Always use a subagent to **verify test results** after any implementation
- When asked to plan, delegate codebase research to a subagent before presenting the plan
- Always use a built-in **plan subagent** in plan mode

---

## Commands

```powershell
# Activate virtual environment (Windows)
expense-tracker\venv\Scripts\Activate.ps1

# Run dev server (http://localhost:5001)
cd expense-tracker
python app.py

# Run all tests
pytest

# Run a specific test file
pytest tests/test_auth.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s
```

---

## Implemented vs Stub Routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

> **Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and Things to Avoid

- **Never use raw string returns** for stub routes once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **Never use f-strings in SQL** — always use `?` parameterized placeholders
- **FK enforcement is manual** — `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not Flask's default 5000 — don't change this
- `style.css` is a single intentional file (~835 lines) — do not split it