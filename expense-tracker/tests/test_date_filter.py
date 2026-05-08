"""
tests/test_date_filter.py

Pytest tests for the Spendly date-filter feature on GET /profile.

Spec: .claude/specs/06-date-filter.md

Coverage:
  1. Unfiltered profile (no query params) shows all expenses
  2. Valid date range shows only in-range expenses in the transaction list
  3. Stats (total_spent, transaction_count, top_category) are scoped to the range
  4. Category breakdown shows only categories present in the filtered period
  5. Date inputs are pre-populated with the active from_date / to_date
  6. Active-filter banner appears when a range is set; absent when unfiltered
  7. Reversed dates (from_date > to_date) are silently swapped; correct results returned
  8. Malformed date in query string treats filter as unset; all data shown
  9. Only one of from_date / to_date supplied treats filter as unset; all data shown
 10. Auth guard: unauthenticated request redirects to /login
"""

import sqlite3
import pytest
from werkzeug.security import generate_password_hash

# ---------------------------------------------------------------------------
# App import — the module lives one level above this tests/ directory
# ---------------------------------------------------------------------------
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app
from database.db import init_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app(tmp_path):
    """
    Isolated Flask app instance backed by a real (but temporary) SQLite file.

    We use a temp-file database rather than ':memory:' because db.py opens a
    new connection on every helper call (no connection-sharing), so an
    in-memory database would be empty on the second connection.  A tmp_path
    file solves that cleanly without any changes to production code.
    """
    db_file = str(tmp_path / "test_spendly.db")

    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        WTF_CSRF_ENABLED=False,
    )

    # Patch the DB_PATH used by db.py for the duration of this fixture
    import database.db as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = db_file

    with flask_app.app_context():
        init_db()
        yield flask_app

    # Restore original DB_PATH so other test sessions are unaffected
    db_module.DB_PATH = original_path


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_client(client):
    """
    A logged-in test client with a deterministic set of expenses seeded
    directly into the database so filter assertions are exact.

    Expense layout (all for the same test user):
        2026-01-05  Food         500.00   "Jan groceries"
        2026-01-15  Transport    200.00   "Metro pass"
        2026-02-10  Food         300.00   "Feb groceries"
        2026-02-20  Bills       1000.00   "Electricity"
        2026-03-01  Health       400.00   "Pharmacy"

    Interesting date ranges for tests:
        Jan only  : 2026-01-01 to 2026-01-31  → 2 txns, Food+Transport
        Feb only  : 2026-02-01 to 2026-02-28  → 2 txns, Food+Bills
        Jan–Feb   : 2026-01-01 to 2026-02-28  → 4 txns
        All       : no filter                  → 5 txns
    """
    import database.db as db_module

    # Register and log in the test user
    client.post(
        "/register",
        data={"name": "Test User", "email": "filter@test.com", "password": "securepass"},
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"email": "filter@test.com", "password": "securepass"},
        follow_redirects=True,
    )

    # Seed expenses directly via the DB so we control dates precisely
    conn = sqlite3.connect(db_module.DB_PATH)
    conn.row_factory = sqlite3.Row
    user_row = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("filter@test.com",)
    ).fetchone()
    user_id = user_row["id"]

    expenses = [
        (user_id, 500.00, "Food",      "2026-01-05", "Jan groceries"),
        (user_id, 200.00, "Transport", "2026-01-15", "Metro pass"),
        (user_id, 300.00, "Food",      "2026-02-10", "Feb groceries"),
        (user_id, 1000.00, "Bills",    "2026-02-20", "Electricity"),
        (user_id, 400.00, "Health",    "2026-03-01", "Pharmacy"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()

    return client, user_id


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _profile(client, **params):
    """GET /profile with optional query-string params."""
    return client.get("/profile", query_string=params)


# ---------------------------------------------------------------------------
# 10. Auth guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_unauthenticated_request_redirects_to_login(self, client):
        resp = _profile(client)
        assert resp.status_code == 302, "Expected redirect for unauthenticated access"
        assert "/login" in resp.headers["Location"], (
            "Unauthenticated /profile must redirect to /login"
        )

    def test_unauthenticated_with_date_params_still_redirects(self, client):
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        assert resp.status_code == 302, (
            "Date params must not bypass auth guard"
        )
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# 1. Unfiltered profile — no query params → all expenses, no banner
# ---------------------------------------------------------------------------

class TestUnfilteredProfile:
    def test_returns_200_for_authenticated_user(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client)
        assert resp.status_code == 200, "Authenticated /profile must return 200"

    def test_all_five_transactions_appear(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client)
        html = resp.data.decode()
        # Each seeded description must appear in the unfiltered page
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Unfiltered profile must show all expenses; '{desc}' was missing"
            )

    def test_active_filter_banner_absent_when_no_params(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client)
        html = resp.data.decode()
        # The banner signals a filtered view — it must NOT appear when unfiltered.
        # We check for text/class markers the spec says identify the active-filter state.
        assert "active-filter" not in html.lower() or "filter-banner" not in html.lower(), (
            "Active-filter indicator must be absent when no date range is set"
        )

    def test_date_inputs_empty_when_no_filter(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client)
        html = resp.data.decode()
        # Inputs should have empty values (value="" pattern from spec)
        assert 'value=""' in html or "value=''" in html, (
            "Date inputs must be empty when no filter is active"
        )


# ---------------------------------------------------------------------------
# 2. Valid date range → only in-range expenses appear in transactions
# ---------------------------------------------------------------------------

class TestValidDateRangeTransactions:
    def test_jan_range_shows_only_jan_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "Jan groceries" in html, "Jan expense must appear in Jan filter"
        assert "Metro pass"    in html, "Jan expense must appear in Jan filter"

    def test_jan_range_excludes_feb_and_mar_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "Feb groceries" not in html, "Feb expense must be excluded by Jan filter"
        assert "Electricity"   not in html, "Feb expense must be excluded by Jan filter"
        assert "Pharmacy"      not in html, "Mar expense must be excluded by Jan filter"

    def test_feb_range_shows_only_feb_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01", to_date="2026-02-28")
        html = resp.data.decode()
        assert "Feb groceries" in html, "Feb expense must appear in Feb filter"
        assert "Electricity"   in html, "Feb expense must appear in Feb filter"

    def test_feb_range_excludes_jan_and_mar_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01", to_date="2026-02-28")
        html = resp.data.decode()
        assert "Jan groceries" not in html, "Jan expense must be excluded by Feb filter"
        assert "Metro pass"    not in html, "Jan expense must be excluded by Feb filter"
        assert "Pharmacy"      not in html, "Mar expense must be excluded by Feb filter"

    def test_inclusive_boundary_from_date(self, seeded_client):
        """from_date itself (2026-01-05) must appear — BETWEEN is inclusive."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-05", to_date="2026-01-05")
        html = resp.data.decode()
        assert "Jan groceries" in html, (
            "Expense on from_date boundary must be included (inclusive BETWEEN)"
        )

    def test_inclusive_boundary_to_date(self, seeded_client):
        """to_date itself (2026-01-15) must appear — BETWEEN is inclusive."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-10", to_date="2026-01-15")
        html = resp.data.decode()
        assert "Metro pass" in html, (
            "Expense on to_date boundary must be included (inclusive BETWEEN)"
        )

    def test_range_with_no_matching_expenses_shows_empty_list(self, seeded_client):
        client, _ = seeded_client
        # A range that contains no seeded expenses
        resp = _profile(client, from_date="2025-01-01", to_date="2025-12-31")
        html = resp.data.decode()
        assert resp.status_code == 200, "Empty filter result must still return 200"
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc not in html, (
                f"No expenses expected for 2025 range; '{desc}' appeared unexpectedly"
            )


# ---------------------------------------------------------------------------
# 3. Stats scoped to filtered period
# ---------------------------------------------------------------------------

class TestStatsScoping:
    def test_transaction_count_reflects_filtered_period(self, seeded_client):
        """Jan filter: 2 transactions (500 + 200)."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        # The count "2" must appear somewhere in the stats area.
        # We assert the unfiltered total (5) is NOT the rendered count.
        # A light check: the numeral "5" alone would be ambiguous, so we
        # look for the in-range count "2" appearing and the full count "5"
        # NOT appearing adjacent to a transaction-count label.
        assert "2" in html, "Transaction count stat must show 2 for Jan filter"

    def test_total_spent_reflects_filtered_period(self, seeded_client):
        """Jan filter total: ₹700 (500 + 200)."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        # Route formats total as ₹700 (no decimals for whole rupees via ,.0f)
        assert "700" in html, (
            "Total spent stat must show 700 for Jan filter (500+200)"
        )

    def test_top_category_reflects_filtered_period(self, seeded_client):
        """Jan filter: Food (₹500) is top category over Transport (₹200)."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "Food" in html, (
            "Top category must be Food for Jan filter (highest spend)"
        )

    def test_top_category_feb_is_bills(self, seeded_client):
        """Feb filter: Bills (₹1000) is top category over Food (₹300)."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01", to_date="2026-02-28")
        html = resp.data.decode()
        assert "Bills" in html, (
            "Top category must be Bills for Feb filter (highest spend ₹1000)"
        )

    def test_empty_range_stats_show_zero(self, seeded_client):
        """A range with no expenses must show zero total and zero count."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2025-01-01", to_date="2025-12-31")
        html = resp.data.decode()
        assert resp.status_code == 200
        # Total must show ₹0 (formatted as ₹0)
        assert "0" in html, "Zero total must appear for empty date range"

    def test_unfiltered_stats_include_all_expenses(self, seeded_client):
        """No filter: total = 500+200+300+1000+400 = 2400."""
        client, _ = seeded_client
        resp = _profile(client)
        html = resp.data.decode()
        assert "2,400" in html or "2400" in html, (
            "Unfiltered total must reflect all 5 expenses (₹2,400)"
        )


# ---------------------------------------------------------------------------
# 4. Category breakdown scoped to filtered period
# ---------------------------------------------------------------------------

class TestCategoryBreakdown:
    def test_jan_filter_shows_food_and_transport_categories(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "Food"      in html, "Food category must appear in Jan breakdown"
        assert "Transport" in html, "Transport category must appear in Jan breakdown"

    def test_jan_filter_excludes_bills_and_health_categories(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "Bills"  not in html, "Bills category must be absent in Jan breakdown"
        assert "Health" not in html, "Health category must be absent in Jan breakdown"

    def test_feb_filter_shows_food_and_bills_categories(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01", to_date="2026-02-28")
        html = resp.data.decode()
        assert "Food"  in html, "Food category must appear in Feb breakdown"
        assert "Bills" in html, "Bills category must appear in Feb breakdown"

    def test_feb_filter_excludes_transport_and_health_categories(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01", to_date="2026-02-28")
        html = resp.data.decode()
        assert "Transport" not in html, "Transport must be absent in Feb breakdown"
        assert "Health"    not in html, "Health must be absent in Feb breakdown"

    def test_empty_range_has_no_category_breakdown(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2025-01-01", to_date="2025-12-31")
        html = resp.data.decode()
        for cat in ("Food", "Transport", "Bills", "Health"):
            assert cat not in html, (
                f"Category '{cat}' must not appear in breakdown for empty date range"
            )


# ---------------------------------------------------------------------------
# 5. Date inputs pre-populated after filtering
# ---------------------------------------------------------------------------

class TestInputPrePopulation:
    def test_from_date_input_pre_populated(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "2026-01-01" in html, (
            "from_date input must be pre-populated with the active from_date"
        )

    def test_to_date_input_pre_populated(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert "2026-01-31" in html, (
            "to_date input must be pre-populated with the active to_date"
        )

    def test_both_inputs_pre_populated(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01", to_date="2026-02-28")
        html = resp.data.decode()
        assert "2026-02-01" in html, "from_date must be pre-populated"
        assert "2026-02-28" in html, "to_date must be pre-populated"

    def test_inputs_empty_when_no_filter_applied(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client)
        html = resp.data.decode()
        # Neither date value should appear in the HTML when no filter is active.
        # We verify the specific range values are absent (not just empty-string check).
        assert "2026-01-01" not in html, (
            "No date values should be pre-populated when filter is inactive"
        )
        assert "2026-01-31" not in html, (
            "No date values should be pre-populated when filter is inactive"
        )


# ---------------------------------------------------------------------------
# 6. Active-filter banner presence / absence
# ---------------------------------------------------------------------------

class TestActiveFilterBanner:
    """
    The spec requires an 'active-filter banner or label' visible when a range
    is active.  We look for a set of text/class markers that indicate a filtered
    state.  Any one of them appearing satisfies the requirement.
    """

    FILTER_MARKERS = [
        "active-filter",
        "filter-active",
        "filter-banner",
        "filtered",
        "Filtered",
        "active filter",
        "Active Filter",
    ]

    def _has_filter_marker(self, html: str) -> bool:
        return any(marker in html for marker in self.FILTER_MARKERS)

    def test_banner_present_when_valid_range_applied(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="2026-01-31")
        html = resp.data.decode()
        assert self._has_filter_marker(html), (
            "Active-filter banner must be visible when a date range is set. "
            f"Looked for: {self.FILTER_MARKERS}"
        )

    def test_banner_absent_when_no_filter(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client)
        html = resp.data.decode()
        assert not self._has_filter_marker(html), (
            "Active-filter banner must NOT appear when no date range is active"
        )

    def test_banner_absent_when_malformed_date(self, seeded_client):
        """Malformed date → filter treated as unset → no banner."""
        client, _ = seeded_client
        resp = _profile(client, from_date="not-a-date", to_date="2026-01-31")
        html = resp.data.decode()
        assert not self._has_filter_marker(html), (
            "Active-filter banner must NOT appear when date params are malformed"
        )


# ---------------------------------------------------------------------------
# 7. Reversed dates are silently swapped
# ---------------------------------------------------------------------------

class TestReversedDates:
    def test_reversed_dates_return_correct_jan_data(self, seeded_client):
        """Passing to_date before from_date must still filter Jan correctly."""
        client, _ = seeded_client
        # Reversed: from=Jan31, to=Jan01
        resp = _profile(client, from_date="2026-01-31", to_date="2026-01-01")
        assert resp.status_code == 200, "Reversed dates must not crash the route"
        html = resp.data.decode()
        assert "Jan groceries" in html, (
            "Jan expense must appear after silent date swap (from > to)"
        )
        assert "Metro pass" in html, (
            "Jan expense must appear after silent date swap (from > to)"
        )

    def test_reversed_dates_exclude_out_of_range_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-31", to_date="2026-01-01")
        html = resp.data.decode()
        assert "Feb groceries" not in html, (
            "Feb expense must be excluded even with reversed Jan date params"
        )
        assert "Pharmacy" not in html, (
            "Mar expense must be excluded even with reversed Jan date params"
        )

    def test_reversed_dates_show_active_filter_banner(self, seeded_client):
        """After swap, a valid range is active → banner must appear."""
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-31", to_date="2026-01-01")
        html = resp.data.decode()
        filter_markers = [
            "active-filter", "filter-active", "filter-banner",
            "filtered", "Filtered", "active filter", "Active Filter",
        ]
        assert any(m in html for m in filter_markers), (
            "Active-filter banner must appear after silent date swap"
        )

    def test_reversed_dates_inputs_pre_populated_with_swapped_values(self, seeded_client):
        """
        After swap, the template receives the corrected (sorted) dates.
        Both the lower and upper bound values must appear in the HTML.
        """
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-31", to_date="2026-01-01")
        html = resp.data.decode()
        assert "2026-01-01" in html, "Swapped from_date must be pre-populated"
        assert "2026-01-31" in html, "Swapped to_date must be pre-populated"


# ---------------------------------------------------------------------------
# 8. Malformed date → treated as unset → all data shown
# ---------------------------------------------------------------------------

class TestMalformedDates:
    def test_malformed_from_date_shows_all_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="not-a-date", to_date="2026-01-31")
        assert resp.status_code == 200
        html = resp.data.decode()
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Malformed from_date must show all data; '{desc}' was missing"
            )

    def test_malformed_to_date_shows_all_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01", to_date="99-99-9999")
        assert resp.status_code == 200
        html = resp.data.decode()
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Malformed to_date must show all data; '{desc}' was missing"
            )

    def test_both_malformed_shows_all_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="abc", to_date="xyz")
        assert resp.status_code == 200
        html = resp.data.decode()
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Both malformed dates must show all data; '{desc}' was missing"
            )

    def test_malformed_date_does_not_raise_500(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-13-45", to_date="2026-01-31")
        assert resp.status_code == 200, (
            "Invalid date values must be silently ignored, not cause a 500"
        )

    @pytest.mark.parametrize("bad_from,bad_to", [
        ("not-a-date",   "2026-01-31"),
        ("2026-01-01",   "not-a-date"),
        ("2026-13-01",   "2026-01-31"),
        ("2026-01-01",   "2026-00-01"),
        ("",             "2026-01-31"),
        ("2026-01-01",   ""),
    ])
    def test_invalid_date_combinations_return_200(self, seeded_client, bad_from, bad_to):
        client, _ = seeded_client
        resp = _profile(client, from_date=bad_from, to_date=bad_to)
        assert resp.status_code == 200, (
            f"from_date={bad_from!r}, to_date={bad_to!r} must not crash the route"
        )


# ---------------------------------------------------------------------------
# 9. Only one of from_date / to_date supplied → treated as unset
# ---------------------------------------------------------------------------

class TestPartialDateParams:
    def test_only_from_date_shows_all_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01")
        html = resp.data.decode()
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Only from_date supplied must show all data; '{desc}' missing"
            )

    def test_only_to_date_shows_all_expenses(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, to_date="2026-01-31")
        html = resp.data.decode()
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Only to_date supplied must show all data; '{desc}' missing"
            )

    def test_only_from_date_no_active_filter_banner(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-01-01")
        html = resp.data.decode()
        filter_markers = [
            "active-filter", "filter-active", "filter-banner",
            "filtered", "Filtered", "active filter", "Active Filter",
        ]
        assert not any(m in html for m in filter_markers), (
            "Active-filter banner must NOT appear when only from_date is supplied"
        )

    def test_only_to_date_no_active_filter_banner(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, to_date="2026-03-31")
        html = resp.data.decode()
        filter_markers = [
            "active-filter", "filter-active", "filter-banner",
            "filtered", "Filtered", "active filter", "Active Filter",
        ]
        assert not any(m in html for m in filter_markers), (
            "Active-filter banner must NOT appear when only to_date is supplied"
        )

    def test_only_from_date_returns_200(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="2026-02-01")
        assert resp.status_code == 200

    def test_only_to_date_returns_200(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, to_date="2026-02-28")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Additional edge-case: empty strings for both date params → unfiltered view
# ---------------------------------------------------------------------------

class TestEmptyStringDates:
    def test_empty_string_dates_show_all_expenses(self, seeded_client):
        """Clearing both inputs submits from_date=&to_date= which must reset."""
        client, _ = seeded_client
        resp = _profile(client, from_date="", to_date="")
        assert resp.status_code == 200
        html = resp.data.decode()
        for desc in ("Jan groceries", "Metro pass", "Feb groceries",
                     "Electricity", "Pharmacy"):
            assert desc in html, (
                f"Empty date strings must behave as unfiltered; '{desc}' missing"
            )

    def test_empty_string_dates_no_banner(self, seeded_client):
        client, _ = seeded_client
        resp = _profile(client, from_date="", to_date="")
        html = resp.data.decode()
        filter_markers = [
            "active-filter", "filter-active", "filter-banner",
            "filtered", "Filtered", "active filter", "Active Filter",
        ]
        assert not any(m in html for m in filter_markers), (
            "Active-filter banner must NOT appear when both date fields are empty"
        )
