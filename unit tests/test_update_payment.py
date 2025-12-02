# tests/test_update_payment.py

import pytest
import mysql.connector
from app import app

"""
TC-3 / UC-3
Pass if:
  - valid payment/mail info updates successfully in DB (UPDATE runs with correct params)
Fail if:
  - invalid info causes DB to not update (no successful UPDATE)
"""

# --------------------------
# Fixtures
# --------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


# --------------------------
# Fake DB helpers (compatible with mysql.connector usage in app.py)
# --------------------------

class FakeCursor:
    def __init__(self):
        self.executed = []           # list of (query, params)
        self.updated_info = None     # last successful update params
        self.raise_on_update = False

    def execute(self, query, params=None):
        self.executed.append((query, params))
        q = (query or "").strip().lower()
        if q.startswith("update"):
            if self.raise_on_update:
                # Simulate DB rejecting the update (e.g. invalid formatting/constraint)
                raise mysql.connector.Error("Simulated DB update failure")
            # simulate successful update: store params
            self.updated_info = params

    def fetchone(self):
        # not used here (update-payment uses UPDATE only)
        return None

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor_obj: FakeCursor):
        self._cursor = cursor_obj

    # app uses cursor(buffered=True) or cursor(dictionary=True, buffered=True)
    def cursor(self, dictionary=False, buffered=False, *args, **kwargs):
        return self._cursor

    def commit(self):
        pass

    def close(self):
        pass

    def is_connected(self):
        return True


# --------------------------
# TEST 1: Valid update succeeds (mail-form then payment-form)
# --------------------------

def test_update_payment_valid(monkeypatch, client):
    # Prepare fake DB cursor & connection
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: conn)

    # Ensure user is "logged in" for the route to return normal template (not redirect)
    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    # 1) POST the mail-form update (fields expected by your app)
    mail_form = {
        "form-identifier": "mail-form",
        "address": "123 Maple Street",
        "address2": "Unit 5",
        "city": "Dallas",
        "state": "TX",
        "postal_code": "75001"
    }

    resp_mail = client.post("/update-payment", data=mail_form, follow_redirects=True)
    assert resp_mail.status_code == 200

    # Verify that an UPDATE query was executed for the mail form with expected params
    found_mail_update = False
    expected_mail_params = ("123 Maple Street", "Unit 5", "Dallas", "TX", "75001", "testuser")
    for q, params in cursor.executed:
        if "update users set address" in (q or "").lower():
            # params should match expected tuple
            assert params == expected_mail_params, f"mail update params mismatch: {params}"
            found_mail_update = True
            break
    assert found_mail_update, "Mail-form UPDATE was not executed."

    # 2) POST the payment-form update (fields expected by your app)
    payment_form = {
        "form-identifier": "payment-form",
        "name": "Jane Doe",               # app splits into first_name, last_name
        "card_number": "4111111111111111",
        "expiration": "12/28",
        "security_code": "123"
    }

    resp_pay = client.post("/update-payment", data=payment_form, follow_redirects=True)
    assert resp_pay.status_code == 200

    # Verify that an UPDATE query was executed for the payment form with expected params
    found_payment_update = False
    expected_payment_params = ("Jane", "Doe", "4111111111111111", "12/28", "123", "testuser")
    for q, params in cursor.executed:
        if "update users set first_name" in (q or "").lower() or "update users set first_name" in (q or ""):
            assert params == expected_payment_params, f"payment update params mismatch: {params}"
            found_payment_update = True
            break

    assert found_payment_update, "Payment-form UPDATE was not executed."


# --------------------------
# TEST 2: Invalid update fails (DB raises on UPDATE) -> no successful update
# --------------------------

def test_update_payment_invalid(monkeypatch, client):
    # Fake cursor that will raise on UPDATE
    failing_cursor = FakeCursor()
    failing_cursor.raise_on_update = True
    failing_conn = FakeConnection(failing_cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: failing_conn)

    # Ensure user is logged in
    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    # Attempt to POST invalid mail-form that triggers DB error
    bad_mail_form = {
        "form-identifier": "mail-form",
        "address": "!?!!",     # invalid characters (we simulate DB rejecting them)
        "address2": "",
        "city": "D@llas",
        "state": "TX",
        "postal_code": "ABCDE"  # non-numeric
    }

    resp = client.post("/update-payment", data=bad_mail_form, follow_redirects=True)
    # The route catches mysql.connector.Error and continues — it should return the template (200)
    assert resp.status_code == 200

    # Because the fake cursor raised, updated_info should remain None (no successful commit)
    assert failing_cursor.updated_info is None, "Invalid data should NOT result in a successful update."

    # The executed list should contain the attempted UPDATE (we append before raising)
    attempted_update = any("update users set address" in (q or "").lower() for q, _ in failing_cursor.executed)
    assert attempted_update, "An UPDATE attempt should have been made (and failed)."
