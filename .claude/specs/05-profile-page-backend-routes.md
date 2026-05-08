# Spec: Profile Page Backend Routes

## Overview
This feature replaces the hardcoded dummy data in the `/profile` route with real database queries. Step 4 built the complete profile UI using static Python dicts; Step 5 wires those same template variables to live data from the `users` and `expenses` tables. New DB helpers are added to `database/db.py` for fetching user info, summary stats, recent transactions, and category breakdowns — keeping all SQL out of `app.py`.

## Depends on
- Step 1: Database setup (`users` and `expenses` tables must exist)
- Step 2: Registration (real user rows must be insertable)
- Step 3: Login + Logout (`session["user_id"]` must be set on login)
- Step 4: Profile Page UI (the template and route structure this step connects to)

## Routes
No new routes. The existing `GET /profile` route is updated to call real DB helpers instead of returning hardcoded data.

## Database changes
No new tables or columns. All data already exists in `users` and `expenses`.

## Templates
- **Modify:** None — `templates/profile.html` receives the same context keys (`user`, `stats`, `transactions`, `categories`) so the template is unchanged.

## Files to change
- `expense-tracker/database/db.py` — add four new query helpers:
  - `get_user_by_id(user_id)` — returns a single user row by primary key
  - `get_user_stats(user_id)` — returns total amount spent, transaction count, and top category name
  - `get_recent_transactions(user_id, limit=5)` — returns the most recent N expense rows ordered by date DESC
  - `get_category_breakdown(user_id)` — returns per-category totals and their percentage of overall spend, ordered by total DESC
- `expense-tracker/app.py` — update `profile_page()` to:
  - Call `get_user_by_id(session["user_id"])` and `abort(404)` if the row is missing
  - Format `user["created_at"]` (stored as `"YYYY-MM-DD HH:MM:SS"`) into `"Month YYYY"` (e.g. `"May 2026"`)
  - Replace all hardcoded dicts/lists with the results of the four new helpers
  - Import the four new helpers at the top of the file

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never f-strings or `%` formatting in SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All SQL belongs in `database/db.py` — none in `app.py`
- `get_recent_transactions` must accept a `limit` parameter (default 5) using `LIMIT ?` in the query
- Category percentages must be computed in SQL using `ROUND(SUM(amount) * 100.0 / total_sum, 0)` or equivalent — not in Python
- `get_user_stats` must use a single query with aggregates (`SUM`, `COUNT`, subquery or window for top category)
- `abort(404)` if `get_user_by_id` returns `None`
- `member_since` must be derived from `users.created_at` — format with Python `datetime.strptime` / `strftime`, not hardcoded

## Definition of done
- [ ] Visiting `/profile` while logged in returns HTTP 200 and shows the logged-in user's real name and email
- [ ] The member-since date on the profile card matches the account's actual `created_at` date (not the hardcoded "January 2026")
- [ ] Total spent stat equals the real sum of that user's expenses in the DB
- [ ] Transaction count stat equals the real count of that user's expense rows
- [ ] Top category stat shows the category with the highest total spend for that user
- [ ] The transaction history table lists the 5 most recent expenses ordered newest-first
- [ ] The category breakdown section shows all categories that user has expenses in, ordered by total spend descending
- [ ] Category percentages in the breakdown sum to approximately 100%
- [ ] Seeding a second user and logging in as them shows only their own data (no data leakage between users)
- [ ] No hardcoded data dicts/lists remain in the `profile_page()` route function in `app.py`
