# tests/test_purchase.py
import pytest
from app import app

# ----------------------
# Fixtures & helpers
# ----------------------
@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


class FakeCursor:
    def __init__(self, role=None, return_email=None):
        self.role = role
        self.return_email = return_email
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        # record the query for optional debugging
        self.executed.append((query, params))

    def fetchone(self):
        if self.role == "select_email":
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
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def is_connected(self):
        return True


class DummySMTP:
    def __init__(self, host, port):
        self.sent = []

    def starttls(self):
        pass

    def login(self, user, pw):
        pass

    def sendmail(self, from_addr, to_addr, msg):
        self.sent.append((from_addr, to_addr, msg))

    def quit(self):
        pass


def purchase_payload(**kwargs):
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
    update_cursor = FakeCursor(role="update")
    insert_cursor = FakeCursor(role="insert")
    select_cursor = FakeCursor(role="select_email", return_email="buyer@example.com")

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
        else:
            return FakeConnection(FakeCursor())

    monkeypatch.setattr("app.mysql.connector.connect", fake_connect)

    dummy_smtp = DummySMTP("smtp.example.com", 587)
    monkeypatch.setattr("app.smtplib.SMTP", lambda host, port: dummy_smtp)

    with client.session_transaction() as sess:
        sess["username"] = "testuser"

    payload = purchase_payload(emailPurchase=True, deliveryCode=-1, vehicleID=42, vehiclePrice="12,345")
    resp = client.post("/purchase-info", json=payload)

    assert resp.status_code == 200
    assert resp.data.decode() == "success"

    # More reliable: check the connections were committed
    assert update_conn.committed, "Stock update should have committed."
    assert insert_conn.committed, "Order insert should have committed."

    # Email send should have been called once
    assert len(dummy_smtp.sent) == 1
    _, to_addr, msg = dummy_smtp.sent[0]
    assert to_addr == "buyer@example.com"
    assert "Online Vehicle Purchase Receipt" in msg


def test_purchase_delivery_only_success(monkeypatch, client):
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

    payload = purchase_payload(emailPurchase=False, deliveryCode=-1)
    resp = client.post("/purchase-info", json=payload)

    assert resp.status_code == 200
    assert resp.data.decode() == "success"

    # Committed flags indicate DB work happened
    assert update_conn.committed
    assert insert_conn.committed


def test_purchase_pickup_mail_email_success(monkeypatch, client):
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

    payload = purchase_payload(emailPurchase=True, deliveryCode=987654, vehicleID=7, vehiclePrice="18,000")
    resp = client.post("/purchase-info", json=payload)

    assert resp.status_code == 200
    assert resp.data.decode() == "success"

    # Email send captured
    assert len(dummy_smtp.sent) == 1
    _, to_addr, msg = dummy_smtp.sent[0]
    assert to_addr == "pickup_buyer@example.com"
    assert ("pick" in msg.lower() and "code" in msg.lower()), "Pickup code should appear in email."

    # Check DB commits as evidence of insert
    assert insert_conn.committed, "Order insert should have committed."


def test_purchase_pickup_only_success(monkeypatch, client):
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
    assert insert_conn.committed


def test_purchase_invalid_request_returns_bad_data(client):
    form = {"address": "some", "card": "data"}
    resp = client.post("/purchase-info", data=form)  # not json
    assert resp.status_code == 400
    assert resp.data.decode().lower() == "bad data"
