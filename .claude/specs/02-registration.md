# Spec: Registration

## Overview
Step 2 converts the existing stub `GET /register` route into a fully working user registration flow. When a visitor submits the registration form, the app validates their input, hashes their password, inserts a new row into the `users` table, and redirects them to the login page. This is the first feature that writes user-generated data to the database and establishes the validation + DB-helper pattern that all subsequent auth routes will follow.

## Depends on
Step 1 — Database Setup (`get_db()`, `init_db()`, and the `users` table must already exist in `database/db.py`).

## Routes
- `POST /register` — process registration form, validate input, insert user — public

The existing `GET /register` route is merged into a single handler accepting both `GET` and `POST`.

## Database changes
No new tables or columns. A new helper function `register_user()` is added to `database/db.py` to keep INSERT logic out of the route.

## Templates
- **Modify:** `templates/register.html`
  - Fix hardcoded `action="/register"` → `action="{{ url_for('register') }}"`
  - Add `value="{{ request.form.get('name', '') }}"` on the name input to preserve the value on error
  - Add `value="{{ request.form.get('email', '') }}"` on the email input to preserve the value on error

## Files to change
- `expense-tracker/app.py`
  - Add `methods=["GET", "POST"]` to the `/register` route
  - Import `request`, `redirect`, `url_for` from Flask
  - Load `SECRET_KEY` from environment and assign to `app.secret_key`
  - Implement POST handler: validate → call `register_user()` → redirect or re-render with error
- `expense-tracker/database/db.py`
  - Add `register_user(name, email, password)` — hashes password, runs parameterised INSERT, returns `None` on success, raises `sqlite3.IntegrityError` on duplicate email
- `expense-tracker/templates/register.html`
  - Fix form action to use `url_for()`
  - Add `value` attributes to name and email inputs

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` is already installed; `python-dotenv` is assumed to be in `requirements.txt`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — `?` placeholders in every SQL statement
- Passwords hashed with `werkzeug.security.generate_password_hash` — never store plaintext
- Use CSS variables — never hardcode hex values in templates or CSS
- All templates extend `base.html`
- Use `abort()` for HTTP errors, not bare string returns
- Use `url_for()` for every internal link — never hardcode paths
- `SECRET_KEY` must be loaded from the `.env` file via `os.environ` or `python-dotenv`
- Validate in this order: name not empty → email contains `@` → password ≥ 8 characters
- On duplicate email: catch `sqlite3.IntegrityError`, re-render form with `error` variable
- On validation failure: re-render form with `error` variable (do not redirect)
- On success: `redirect(url_for('login'))`
- All DB logic (the INSERT) must live in `database/db.py`, not in the route function

## Definition of done
- [ ] `GET /register` still renders the form (no regression)
- [ ] Submitting a valid name, email, and password (≥ 8 chars) creates a new row in the `users` table
- [ ] After successful registration, the browser is redirected to `/login`
- [ ] Submitting an already-registered email re-renders the form with a visible error message
- [ ] Submitting an empty name shows a validation error
- [ ] Submitting a password shorter than 8 characters shows a validation error
- [ ] On error, the name and email fields retain the values the user typed (password field intentionally cleared)
- [ ] The `password_hash` column in the DB contains a hashed value, not the plaintext password
- [ ] No hardcoded `/register` URL in the template — `url_for('register')` is used
