# tests/test_vehicle_inventory.py
import pytest
import mysql.connector
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # session must indicate admin using exactly this key/value
        with client.session_transaction() as sess:
            sess["username"] = "Admin"
        yield client


# --- Fake DB helpers compatible with app.py usage ---
class FakeCursor:
    def __init__(self):
        self.executed = []
        self.raise_on_update = False

    def execute(self, query, params=None):
        # record the query (so tests can inspect it)
        self.executed.append((query, params))
        q = (query or "").strip().lower()
        if q.startswith("update") and self.raise_on_update:
            # simulate DB rejecting invalid input
            raise mysql.connector.Error("Simulated DB error on UPDATE")

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor_obj):
        self._cursor = cursor_obj
        self.committed = False
        self.closed = False

    # app calls cnx.cursor(buffered=True) or cursor(dictionary=True, buffered=True)
    def cursor(self, buffered=False, dictionary=False, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def is_connected(self):
        return True


def test_update_vehicle_success(monkeypatch, client):
    """
    Admin posts valid vehicle data. The app should run an UPDATE and call commit().
    """
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    # Patch mysql.connector.connect used in app.py
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: conn)

    # The vehicle-inventory route expects 'name', 'stock', 'price' in the form
    form_data = {
        "name": "Toyota Camry",
        "stock": "10",
        "price": "25000"
    }

    resp = client.post("/vehicle-inventory", data=form_data, follow_redirects=True)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}. Body: {resp.data[:200]!r}"

    # Ensure an UPDATE was executed
    updates = [q for q, _ in cursor.executed if (q or "").strip().lower().startswith("update")]
    assert len(updates) >= 1, f"No UPDATE executed, queries: {cursor.executed}"

    # Ensure commit() was called on connection
    assert conn.committed, "Expected commit() to be called after successful update."


def test_update_vehicle_invalid_input(monkeypatch, client):
    """
    Admin posts invalid characters. Simulate DB raising an error on UPDATE.
    The app should handle the exception and not call commit().
    """
    failing_cursor = FakeCursor()
    failing_cursor.raise_on_update = True
    failing_conn = FakeConnection(failing_cursor)

    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: failing_conn)

    bad_form = {
        "name": "Toyota Camry",
        "stock": "1O",     # letter O instead of zero
        "price": "25!00",  # invalid character
    }

    resp = client.post("/vehicle-inventory", data=bad_form, follow_redirects=True)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}. Body: {resp.data[:200]!r}"

    # The UPDATE should have been attempted (execute appended before raise)
    attempted_updates = [q for q, _ in failing_cursor.executed if (q or "").strip().lower().startswith("update")]
    assert len(attempted_updates) >= 1, "An UPDATE attempt should have been made (and failed)."

    # commit should not be called because the update raised
    assert not failing_conn.committed, "Commit should NOT have been called when DB raised an error."
