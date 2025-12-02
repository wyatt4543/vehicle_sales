# tests/test_purchase_api.py
import pytest
import json
import types

from app import app

# ----------------------
# Fixtures
# ----------------------
@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

# ----------------------
# Fake DB / SMTP helpers
# ----------------------

class FakeCursor:
    def __init__(self, role=None, return_email=None):
        """
        role: str label for what this cursor is used for ("update","insert","select_email")
        return_email: if role == "select_email", this value will be returned by fetchone()
        """
        self.role = role
        self.return_email = return_email
        self.executed = []  # list of (query, params)
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

        # simulate raising on bad queries? not necessary here

    def fetchone(self):
        # used only for SELECT email in app.purchase_info
        if self.role == "select_email":
            # app expects cursor.fetchone() -> a tuple-like result
            if self.return_email is None:
                return None
            return (self.return_email,)
        return None

    def fetchall(self):
        return []

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor_obj):
        self._cursor = cursor_obj
        self.committed = False
        self.closed = False

    def cursor(self, dictionary=False, buffered=False):
        # app uses cursor(buffered=True) or cursor(dictionary=True, buffered=True)
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def is_connected(self):
        return True


class DummySMTP:
    """A dummy SMTP class to capture email send attempts."""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.started_tls = False
        self.logged_in = False
        self.sent = []  # list of (from_addr, to_addr, message)
        self.closed = False

    def starttls(self):
        self.started_tls = True

    def login(self, user, pw):
        self.logged_in = True

    def sendmail(self, from_addr, to_addr, msg):
        self.sent.append((from_addr, to_addr, msg))

    def quit(self):
        self.closed = True

# ----------------------
# Helper: build JSON payload used by purchase-info route
# ----------------------
def purchase_payload(**kwargs):
    # default payload fields used by app.purchase_info
    payload = {
        "emailPurchase": kwargs.get("emailPurchase", False),
        "customer": kwargs.get("customer", "Test Customer"),
        "vehicleName": kwargs.get("vehicleName", "Alpha One"),
        "vehiclePrice": kwargs.get("vehiclePrice", "10000"),
        "deliveryCode": kwargs.get("deliveryCode", -1),
        "vehicleID": kwargs.get("vehicleID", 1)
    }
    return payload

# ----------------------
# Tests
# ----------------------

def test_purchase_delivery_mail_email_success(monkeypatch, client):
    """
    Valid purchase: delivery + mailed receipt + emailed receipt.
    Expect: 200 and 'success' return value. Email send should be attempted.
    """

    # Prepare three fake connections/cursors:
    # 1) update stock (role "update")
    # 2) insert order (role "insert")
    # 3) select email (role "select_email") -> returns an email address
    update_cursor = FakeCursor(role="update")
    insert_cursor = FakeCursor(role="insert")
    select_cursor = FakeCursor(role="select_email", return_email="buyer@example.com")

    update_conn = FakeConnection(update_cursor)
    insert_conn = FakeConnection(insert_cursor)
    select_conn = FakeConnection(select_cursor)

    # connect_count will let us return the right connection for each call
    connect_state = {"count": 0}
    def fake_connect(**kwargs):
        c = connect_state["count"]
        connect_state["count"] += 1
        if c == 0:
            return update_conn
        elif c == 1:
            return insert_conn
        elif c == 2:
            return select_conn
        else:
            # default fallback
            return FakeConnection(FakeCursor())

    # monkeypatch DB connect and SMTP in app
    monkeypatch.setattr("app.mysql.connector.connect", fake_connect)
    dummy_smtp = DummySMTP("smtp.example.com", 587)
    monkeypatch.setattr("app.smtplib.SMTP", lambda host, port: dummy_smtp)

    # ensure session has username
    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    payload = purchase_payload(emailPurchase=True, deliveryCode=-1, vehicleID=42, vehiclePrice="12,345")
    resp = client.post("/purchase-info", json=payload)

    # Should be success
    assert resp.status_code == 200
    assert resp.data.decode() == "success"

    # Verify the update query (stock decrement) executed once
    assert any("UPDATE vehicles" in (q or "").upper() for q, _ in update_cursor.executed)

    # Verify an order INSERT was executed
    assert any("INSERT INTO orders" in (q or "").upper() for q, _ in insert_cursor.executed)

    # Because emailPurchase=True, SMTP.sendmail should have been called
    assert len(dummy_smtp.sent) == 1
    from_addr, to_addr, msg = dummy_smtp.sent[0]
    assert to_addr == "buyer@example.com"
    assert "Online Vehicle Purchase Receipt" in msg

def test_purchase_delivery_only_success(monkeypatch, client):
    """
    Valid purchase: delivery only, no email. Should succeed and NOT send email.
    """
    # Setup fake DB connections for update & insert only
    update_cursor = FakeCursor(role="update")
    insert_cursor = FakeCursor(role="insert")
    update_conn = FakeConnection(update_cursor)
    insert_conn = FakeConnection(insert_cursor)
    connect_state = {"count": 0}
    def fake_connect(**kwargs):
        c = connect_state["count"]
        connect_state["count"] += 1
        if c == 0:
            return update_conn
        else:
            return insert_conn

    monkeypatch.setattr("app.mysql.connector.connect", fake_connect)
    # patch SMTP to ensure it would be available if called (should not be)
    monkeypatch.setattr("app.smtplib.SMTP", lambda host, port: DummySMTP(host, port))

    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    payload = purchase_payload(emailPurchase=False, deliveryCode=-1)
    resp = client.post("/purchase-info", json=payload)

    assert resp.status_code == 200
    assert resp.data.decode() == "success"

def test_purchase_pickup_mail_email_success(monkeypatch, client):
    """
    Valid purchase: pickup + mail + email (deliveryCode provided).
    Email text should include the pickup code.
    """
    update_cursor = FakeCursor(role="update")
    insert_cursor = FakeCursor(role="insert")
    select_cursor = FakeCursor(role="select_email", return_email="pickup_buyer@example.com")
    update_conn = FakeConnection(update_cursor)
    insert_conn = FakeConnection(insert_cursor)
    select_conn = FakeConnection(select_cursor)

    connect_state = {"count": 0}
    def fake_connect(**kwargs):
        c = connect_state["count"]
        connect_state["count"] += 1
        if c == 0:
            return update_conn
        elif c == 1:
            return insert_conn
        elif c == 2:
            return select_conn
        return FakeConnection(FakeCursor())

    monkeypatch.setattr("app.mysql.connector.connect", fake_connect)

    dummy_smtp = DummySMTP("smtp.example.com", 587)
    monkeypatch.setattr("app.smtplib.SMTP", lambda host, port: dummy_smtp)

    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    # Provide a deliveryCode (pickup code) different from -1
    payload = purchase_payload(emailPurchase=True, deliveryCode=987654, vehicleID=7, vehiclePrice="18,000")
    resp = client.post("/purchase-info", json=payload)

    assert resp.status_code == 200
    assert resp.data.decode() == "success"

    # Email should contain pickup code string
    assert len(dummy_smtp.sent) == 1
    _, to_addr, msg = dummy_smtp.sent[0]
    assert to_addr == "pickup_buyer@example.com"
    assert "pick-up code" in msg.lower() or "pick up code" in msg.lower() or "pick-up" in msg.lower() or "pick up" in msg.lower()
    # also ensure order insert happened
    assert any("INSERT INTO orders" in (q or "").upper() for q, _ in insert_cursor.executed)

def test_purchase_pickup_only_success(monkeypatch, client):
    """
    Valid purchase: pickup only (no email/mail). Should succeed and not send email.
    """
    update_cursor = FakeCursor(role="update")
    insert_cursor = FakeCursor(role="insert")
    update_conn = FakeConnection(update_cursor)
    insert_conn = FakeConnection(insert_cursor)

    connect_state = {"count": 0}
    def fake_connect(**kwargs):
        c = connect_state["count"]
        connect_state["count"] += 1
        if c == 0:
            return update_conn
        else:
            return insert_conn

    monkeypatch.setattr("app.mysql.connector.connect", fake_connect)
    monkeypatch.setattr("app.smtplib.SMTP", lambda host, port: DummySMTP(host, port))

    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    payload = purchase_payload(emailPurchase=False, deliveryCode=5555, vehicleID=9)
    resp = client.post("/purchase-info", json=payload)

    assert resp.status_code == 200
    assert resp.data.decode() == "success"

def test_purchase_invalid_request_returns_bad_data(client):
    """
    If the request is not JSON, app.purchase_info returns 'bad data' with status 400.
    """
    # Post form-encoded data (not JSON)
    form = {
        "address": "some",
        "card": "data"
    }

    resp = client.post("/purchase-info", data=form)  # not json
    assert resp.status_code == 400
    assert resp.data.decode().lower() == "bad data"
