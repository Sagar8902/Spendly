# Spec: Login and Logout

## Overview
Step 3 converts the stub `GET /login` route into a full login flow and implements the `GET /logout` stub. When a user submits the login form, the app looks up their account by email, verifies the password hash, and stores the user's ID in the Flask session. Logging out clears the session and redirects to the landing page. This establishes the session-based authentication foundation that all protected routes in later steps will rely on.

## Depends on
- Step 1 — Database Setup (`get_db()`, `init_db()`, `users` table)
- Step 2 — Registration (`register_user()`, `password_hash` column, user rows in the DB)

## Routes
- `POST /login` — process login form, verify credentials, create session — public
- `GET /logout` — clear session, redirect to landing — public (no auth required to call)

The existing `GET /login` stub is merged into a single handler accepting both `GET` and `POST`.

## Database changes
No new tables or columns. A new helper function `get_user_by_email(email)` is added to `database/db.py` to keep the SELECT logic out of the route.

## Templates
- **Modify:** `templates/login.html`
  - Add `method="POST"` and `action="{{ url_for('login') }}"` to the form tag
  - Add `value="{{ email or '' }}"` on the email input to preserve the value on error
  - Display `{{ error }}` in an error banner when the variable is present

## Files to change
- `expense-tracker/app.py`
  - Add `session` to the Flask imports
  - Add `check_password_hash` import from `werkzeug.security` (or let db.py handle it)
  - Add `get_user_by_email` to the `database.db` import line
  - Expand `GET /login` to accept `methods=["GET", "POST"]`
  - Implement POST handler: call `get_user_by_email()`, verify hash, set `session['user_id']`, redirect or re-render with error
  - Implement `GET /logout`: clear session with `session.clear()`, redirect to `url_for('landing')`
- `expense-tracker/database/db.py`
  - Add `get_user_by_email(email)` — parameterised SELECT, returns a `sqlite3.Row` or `None`
- `expense-tracker/templates/login.html`
  - Fix form to POST with `url_for('login')`
  - Add value retention on the email field
  - Add error banner for `{{ error }}`

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` is already available via the existing `werkzeug` install.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — `?` placeholders in every SQL statement
- Password verification with `werkzeug.security.check_password_hash` — never compare plaintext
- Use a single generic error message for both "email not found" and "wrong password" to avoid user enumeration (e.g. "Invalid email or password.")
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `abort()` for HTTP errors, not bare string returns
- Use `url_for()` for every internal link — never hardcode paths
- Session key must be `'user_id'` (integer) — no other auth data in the session
- On successful login: `redirect(url_for('landing'))` (dashboard not built yet)
- On failed login: re-render `login.html` with `error` and preserve the submitted `email` value
- `logout` must call `session.clear()`, not `session.pop('user_id')`, to wipe the full session
- All DB logic must live in `database/db.py`, not in the route function

## Definition of done
- [ ] `GET /login` still renders the login form (no regression)
- [ ] Submitting a valid email and correct password creates `session['user_id']` and redirects to `/`
- [ ] Submitting a valid email with the wrong password re-renders the form with a generic error message
- [ ] Submitting an email that does not exist re-renders the form with the same generic error message (no user enumeration)
- [ ] On error, the email field retains the value the user typed (password field intentionally cleared)
- [ ] `GET /logout` clears the session and redirects to the landing page
- [ ] After logout, the session no longer contains `user_id`
- [ ] The demo seed user (`demo@spendly.com` / `demo123`) can log in successfully
- [ ] No hardcoded URLs in the template — `url_for()` is used throughout
