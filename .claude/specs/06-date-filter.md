# Spec: Date Filter on Profile Page

## Overview
This feature adds a date-range filter to the profile page so users can narrow the stats, transaction history, and category breakdown to a specific period. A compact filter form (from/to date inputs + a submit button) sits between the stats cards and the transaction section. On submit it reloads `/profile` with `from_date` and `to_date` query-string parameters; the route reads those params, validates them, passes them to each DB helper, and re-renders the same template with filtered data. When no params are present the page behaves exactly as before.

## Depends on
- Step 1: Database setup (`expenses` table with `date` TEXT column in `YYYY-MM-DD` format)
- Step 4: Profile Page UI (template structure this feature adds a filter form to)
- Step 5: Profile Page Backend Routes (DB helpers this feature extends with date-range support)

## Routes
No new routes. The existing `GET /profile` route gains optional query-string parameters:
- `from_date` — ISO date string `YYYY-MM-DD`, inclusive lower bound (optional)
- `to_date`   — ISO date string `YYYY-MM-DD`, inclusive upper bound (optional)

## Database changes
No new tables or columns. All four existing query helpers gain optional `from_date` / `to_date` parameters that append `AND date BETWEEN ? AND ?` when both values are provided.

## Templates
- **Modify:** `templates/profile.html` — add a date-filter form between the stats section and the "Recent Transactions" section:
  - Two `<input type="date">` fields (from / to)
  - A submit button
  - Pre-populate inputs with current `from_date` / `to_date` values if set
  - Show an active-filter banner/label when a range is active so the user knows the data is filtered
- **Modify:** `templates/profile.html` — update the section title "Recent Transactions" to reflect the filter state (e.g. "Transactions" with a count suffix or filter note) — optional, but the active-filter banner is required

## Files to change
- `expense-tracker/database/db.py` — update four helpers to accept optional date-range params:
  - `get_user_stats(user_id, from_date=None, to_date=None)`
  - `get_recent_transactions(user_id, limit=5, from_date=None, to_date=None)` — when a date range is active, remove the `LIMIT` cap and return all matching rows so the user sees every transaction in the period
  - `get_category_breakdown(user_id, from_date=None, to_date=None)`
  - `get_user_by_id` — unchanged; user identity is not date-scoped
- `expense-tracker/app.py` — update `profile_page()` to:
  - Read `from_date` and `to_date` from `request.args`
  - Validate both values are valid `YYYY-MM-DD` dates; if either is malformed, ignore it (treat as unset) rather than raising an error
  - Validate that `from_date <= to_date`; if not, swap them silently
  - Pass validated `from_date` / `to_date` to all three stat/query helpers
  - Pass `from_date` and `to_date` back to the template context so the form can re-populate its inputs

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never f-strings or `%` formatting in SQL; date values must go through `?` placeholders
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All SQL belongs in `database/db.py` — none in `app.py`
- Date filtering uses SQLite `BETWEEN ? AND ?` on the `date` TEXT column (ISO format sorts correctly as text)
- When only one of `from_date` / `to_date` is supplied, ignore both — require a complete range or no range
- When a range is active, `get_recent_transactions` must lift the `LIMIT` and return all rows in the period
- The filter form must use `method="GET"` and `action="{{ url_for('profile_page') }}"` — no JS required
- Input pre-population: `value="{{ from_date or '' }}"` pattern; no extra Jinja gymnastics
- Active-filter state: pass a boolean `filtered` (or just check `from_date and to_date` in the template) so the banner only renders when a range is active

## Definition of done
- [ ] Visiting `/profile` with no query params shows all data — identical to Step 5 behaviour
- [ ] Submitting the filter form with a valid from/to range reloads the page and shows only expenses within that range in the transaction table
- [ ] Stats (total spent, transaction count, top category) reflect only the filtered period when a range is active
- [ ] Category breakdown shows only categories that have expenses in the filtered period
- [ ] The two date inputs are pre-populated with the active `from_date` and `to_date` values after filtering
- [ ] An active-filter banner or label is visible on the page when a date range is applied
- [ ] Submitting with `from_date > to_date` still works (values are silently swapped)
- [ ] Submitting with a malformed date (e.g. `from_date=not-a-date`) treats the filter as unset and shows all data
- [ ] Clearing both inputs and submitting returns to the unfiltered view
- [ ] No raw SQL appears in `app.py`
