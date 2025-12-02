# tests/test_update_user.py
import pytest
import mysql.connector
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


# Fake DB helpers compatible with app.py usage
class FakeCursor:
    def __init__(self):
        self.executed = []        # list of (query, params)
        self.raise_on_update = False
        self.fetchone_ret = None

    def execute(self, query, params=None):
        self.executed.append((query, params))
        q = (query or "").strip().lower()
        if q.startswith("update") and self.raise_on_update:
            # simulate DB rejecting invalid characters / constraint failures
            raise mysql.connector.Error("Simulated DB error on UPDATE")

    def fetchone(self):
        return self.fetchone_ret

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor_obj: FakeCursor):
        self._cursor = cursor_obj
        self.committed = False
        self.closed = False

    # match signature used in app: cursor(dictionary=True, buffered=True)
    def cursor(self, dictionary=False, buffered=False, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def is_connected(self):
        return True


def test_admin_can_update_user(monkeypatch, client):
    """
    Admin updates a user's information successfully.
    session['username'] must be 'Admin' (only this session key is set).
    The route should execute an UPDATE and call commit().
    """
    fake_cursor = FakeCursor()
    fake_conn = FakeConnection(fake_cursor)

    # monkeypatch mysql.connector.connect used in app.py
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: fake_conn)

    # ensure admin session only uses session['username'] == 'Admin'
    with client.session_transaction() as sess:
        sess["username"] = "Admin"

    form = {
        "first-name": "Alice",
        "last-name": "Johnson",
        "new-username": "alicej",
        "email": "alice@example.com",
        "username": "test_user_to_update"
    }

    resp = client.post("/update-user", data=form, follow_redirects=True)

    # app returns the template for Admin after POST; expect 200
    assert resp.status_code == 200

    # Verify an UPDATE query was attempted and commit occurred
    updates = [q for q, _ in fake_cursor.executed if (q or "").strip().lower().startswith("update")]
    assert len(updates) >= 1, f"No UPDATE executed, queries: {fake_cursor.executed}"
    assert fake_conn.committed, "Expected commit() to be called after successful update."


def test_admin_update_invalid_characters(monkeypatch, client):
    """
    Admin attempts to update a user with invalid characters.
    Simulate DB raising an error on UPDATE. The app should handle it and not call commit().
    """
    failing_cursor = FakeCursor()
    failing_cursor.raise_on_update = True
    failing_conn = FakeConnection(failing_cursor)

    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: failing_conn)

    with client.session_transaction() as sess:
        sess["username"] = "Admin"

    bad_form = {
        "first-name": "B@d!",
        "last-name": "Us#r",
        "new-username": "bad$user!!",
        "email": "bad@@example",
        "username": "target_user"
    }

    resp = client.post("/update-user", data=bad_form, follow_redirects=True)

    # The app should catch mysql.connector.Error and still return the admin template.
    assert resp.status_code == 200

    # Because the fake cursor raised on UPDATE, commit should NOT be called
    assert not failing_conn.committed, "Commit should not have been called when DB raised an error."

    # The attempted UPDATE should still be recorded (execute appended before raising)
    attempted_updates = [q for q, _ in failing_cursor.executed if (q or "").strip().lower().startswith("update")]
    assert len(attempted_updates) >= 1, "An UPDATE attempt should have been made (and failed)."
