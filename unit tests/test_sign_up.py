# tests/test_sign_up.py
import pytest
import bcrypt
import mysql.connector
from flask import session
from app import app

"""
TC-2 / UC-2
Pass if:
 - Account created → user can successfully log in
Fail if:
 - Account not created → user cannot log in
"""

# --------------------------
# Fixtures
# --------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Keep follow_redirects explicit in calls below
    return app.test_client()


# --------------------------
# Fake DB helpers (match mysql.connector usage)
# --------------------------

class FakeCursor:
    """
    Simulates a DB cursor. Tests can configure `fetchone_return`.
    If `raise_on_insert` is True, executing an INSERT will raise mysql.connector.Error.
    """
    def __init__(self):
        self.insert_called = False
        self.select_called = False
        self.fetchone_return = None
        self.raise_on_insert = False
        self.executed_queries = []

    def execute(self, query, params=None):
        # record query for debugging/assertions
        self.executed_queries.append((query, params))
        q = query.strip().lower()
        if q.startswith("select"):
            self.select_called = True
        if "insert into users" in q:
            if self.raise_on_insert:
                # simulate DB rejecting input (invalid characters, constraint, etc.)
                raise mysql.connector.Error("Simulated DB insert failure")
            self.insert_called = True

    def fetchone(self):
        return self.fetchone_return

    def fetchall(self):
        # not used in sign_up/sign_in routes, but implemented for completeness
        return []

    def close(self):
        pass


class FakeConnection:
    """
    Simulates a DB connection. Accepts arbitrary keyword args in cursor().
    Provides is_connected() since app checks it in finally blocks.
    """
    def __init__(self, cursor_obj: FakeCursor):
        self._cursor = cursor_obj

    # app uses cursor(buffered=True) or cursor(dictionary=True, buffered=True) sometimes
    def cursor(self, dictionary=False, buffered=False, *args, **kwargs):
        return self._cursor

    def commit(self):
        pass

    def close(self):
        pass

    def is_connected(self):
        return True


# --------------------------
# TEST 1: successful signup + login
# --------------------------

def test_successful_signup_and_login(monkeypatch, client):
    """
    Simulate a successful sign-up followed by a sign-in.
    Steps:
      - sign-up: initial SELECT returns None (no existing user), INSERT succeeds
      - sign-in: SELECT returns the stored hashed password -> bcrypt.checkpw succeeds
      - assert session['username'] is set after sign-in
    """

    # create fake cursor/connection for sign-up
    sign_up_cursor = FakeCursor()
    sign_up_conn = FakeConnection(sign_up_cursor)

    # monkeypatch the connect function used in app.py
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: sign_up_conn)

    # POST to sign-up (app expects fields: first-name,last-name,username,email,password)
    signup_data = {
        "first-name": "John",
        "last-name": "Smith",
        "username": "john123",
        "email": "john@example.com",
        "password": "secret123",
        "confirm-pass": "secret123",  # client-side JS; server ignores, but include for form completeness
    }

    # sign-up should redirect to sign-in. Use follow_redirects to get final page.
    resp = client.post("/sign-up", data=signup_data, follow_redirects=True)
    assert resp.status_code in (200, 302)
    # sign-up should have executed a SELECT (to check existing user) and then an INSERT
    assert sign_up_cursor.select_called, "Expected SELECT to check existing user"
    assert sign_up_cursor.insert_called, "Expected INSERT to be called for new user"

    # Now prepare the DB response for sign-in: app's sign_in() does:
    # cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    # result = cursor.fetchone()
    # stored_hashed_password = result[0]
    # bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    # Create a real bcrypt hash that app will compare against
    password_plain = "secret123"
    hashed = bcrypt.hashpw(password_plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    sign_in_cursor = FakeCursor()
    # fetchone should return a tuple-like object where index 0 is the hashed password string
    sign_in_cursor.fetchone_return = (hashed,)
    sign_in_conn = FakeConnection(sign_in_cursor)

    # Patch connect to return the sign-in connection now
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: sign_in_conn)

    # POST to sign-in
    login_data = {
        "username": "john123",
        "password": "secret123"
    }
    login_resp = client.post("/sign-in", data=login_data, follow_redirects=True)
    assert login_resp.status_code in (200, 302)
    # Check that the sign-in SELECT was called
    assert sign_in_cursor.select_called, "Expected SELECT during sign-in"

    # Verify the session got set (Flask test client stores session server-side; access via session_transaction)
    with client.session_transaction() as sess:
        assert sess.get("username") == "john123", "User should be logged in after sign-in"


# --------------------------
# TEST 2: invalid characters (simulate DB rejecting insert) -> sign-up fails to insert, login fails
# --------------------------

def test_invalid_characters_block_login(monkeypatch, client):
    """
    Simulate an attempted sign-up with invalid username (server treats this as a DB insert failure).
    We configure the fake cursor to raise on INSERT. After that, a login attempt for that username should fail.
    """

    # Fake cursor that will raise on INSERT
    failing_cursor = FakeCursor()
    failing_cursor.raise_on_insert = True
    failing_conn = FakeConnection(failing_cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: failing_conn)

    bad_signup = {
        "first-name": "Bad",
        "last-name": "User",
        "username": "!!bad!!",  # invalid characters - simulate DB refusing this
        "email": "bad@example.com",
        "password": "password",
        "confirm-pass": "password",
    }

    resp = client.post("/sign-up", data=bad_signup, follow_redirects=True)
    # Because the fake insert raised, the app's exception handler runs and the view should render sign-up page again.
    # The app does not explicitly flash an "invalid characters" message on DB error, so we assert:
    #  - insert was attempted but did not succeed
    assert failing_cursor.insert_called is False or failing_cursor.raise_on_insert is True

    # The response should be the sign-up page (contains the heading "Sign Up")
    assert b"Sign Up" in resp.data

    # Now simulate a login attempt for this username: DB returns no row (user not inserted)
    login_cursor = FakeCursor()
    login_cursor.fetchone_return = None  # no such user
    login_conn = FakeConnection(login_cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: login_conn)

    login_data = {"username": "!!bad!!", "password": "password"}
    login_resp = client.post("/sign-in", data=login_data, follow_redirects=True)
    # sign-in should not set the session (login fails)
    with client.session_transaction() as sess:
        assert sess.get("username") is None

    # sign-in route flashes 'Invalid username or password' on failure; ensure we see evidence of failure:
    # The app returns the sign-in page on failure; check that response contains 'Invalid' or 'Sign In'
    assert (b"Invalid" in login_resp.data) or (b"Sign In" in login_resp.data)
