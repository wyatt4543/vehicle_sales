# tests/test_integration_flows.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import bcrypt
import json
from app import app

# ---------------------------
# Lightweight DB & SMTP fakes
# ---------------------------
class SimpleCursor:
    def __init__(self, rows=None, fetchone_value=None):
        # rows returned by fetchall (list/dict depending on use)
        self._rows = rows if rows is not None else []
        # value returned by fetchone (tuple or None)
        self._fetchone = fetchone_value
        self.executed = []  # list of (query, params)
        self.closed = False

    def execute(self, query, params=None):
        # record query for later assertions
        self.executed.append((query, params))

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._fetchone

    def close(self):
        self.closed = True


class SimpleConnection:
    def __init__(self, cursor: SimpleCursor):
        self._cursor = cursor
        self.committed = False
        self.closed = False

    # match any signature (dictionary=True, buffered=True, etc.)
    def cursor(self, *args, **kwargs):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def is_connected(self):
        return True


class SequenceConnector:
    """
    Callable used to monkeypatch mysql.connector.connect.
    Returns successive connections from the provided list each time it's called.
    After the list is exhausted, it returns the last connection repeatedly.
    """
    def __init__(self, connections):
        self._conns = list(connections)
        self._idx = 0

    def __call__(self, **kwargs):
        if self._idx < len(self._conns):
            conn = self._conns[self._idx]
            self._idx += 1
            return conn
        return self._conns[-1]


class DummySMTP:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.started = False
        self.logged = False
        self.sent = []

    def starttls(self):
        self.started = True

    def login(self, user, pw):
        self.logged = True

    def sendmail(self, from_addr, to_addr, msg):
        self.sent.append((from_addr, to_addr, msg))

    def quit(self):
        pass


# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "integration-test-key"
    return app.test_client()


# ---------------------------
# Integration-style tests
# ---------------------------
def test_signup_signin_then_purchase_flow(monkeypatch, client):
    """
    Integration flow:
      - sign up (DB INSERT)
      - sign in (DB SELECT returns hashed password)
      - make a purchase with email (stock update, order insert, select email, SMTP send)
    """
    # 1) Sign-up: fake connection that will accept select + insert
    signup_cursor = SimpleCursor(fetchone_value=None)
    signup_conn = SimpleConnection(signup_cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: signup_conn)

    signup_form = {
        "first-name": "Integrate",
        "last-name": "Tester",
        "username": "int_user",
        "email": "int@example.com",
        "password": "integpass"
    }

    resp = client.post("/sign-up", data=signup_form, follow_redirects=True)
    assert resp.status_code in (200, 302)
    # ensure sign-up ran a SELECT (to check existing) and attempted an INSERT
    executed_qs = [q for q, _ in signup_cursor.executed]
    assert any("select" in (q or "").lower() for q in executed_qs), "signup should SELECT to check existing user"
    assert any("insert into users" in (q or "").lower() for q in executed_qs), "signup should INSERT new user"

    # 2) Sign-in: prepare a real bcrypt hash and return it on SELECT
    password_plain = "integpass"
    hashed = bcrypt.hashpw(password_plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    signin_cursor = SimpleCursor(fetchone_value=(hashed,))
    signin_conn = SimpleConnection(signin_cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: signin_conn)

    login_form = {"username": "int_user", "password": "integpass"}
    login_resp = client.post("/sign-in", data=login_form, follow_redirects=True)
    assert login_resp.status_code in (200, 302)
    # session should now contain the username
    with client.session_transaction() as sess:
        assert sess.get("username") == "int_user"

    # 3) Purchase flow: we need three DB connections in order:
    #    - update stock (UPDATE)
    #    - insert order (INSERT)
    #    - select user's email (SELECT email)
    update_cursor = SimpleCursor()
    insert_cursor = SimpleCursor()
    select_cursor = SimpleCursor(fetchone_value=("int@example.com",))
    update_conn = SimpleConnection(update_cursor)
    insert_conn = SimpleConnection(insert_cursor)
    select_conn = SimpleConnection(select_cursor)

    seq = SequenceConnector([update_conn, insert_conn, select_conn])
    monkeypatch.setattr("app.mysql.connector.connect", seq)

    # patch SMTP to our DummySMTP
    dummy_smtp = DummySMTP("smtp.gmail.com", 587)
    monkeypatch.setattr("app.smtplib.SMTP", lambda host, port: dummy_smtp)

    purchase_payload = {
        "emailPurchase": True,
        "customer": "Integrate Tester",
        "vehicleName": "Integrate One",
        "vehiclePrice": "9,999",
        "deliveryCode": -1,
        "vehicleID": 123
    }

    resp = client.post("/purchase-info", json=purchase_payload)
    assert resp.status_code == 200
    assert resp.data.decode() == "success"

    # Verify DB update and insert were attempted
    assert any("update vehicles set stock" in (q or "").lower() or "update vehicles set stock = stock - 1" in (q or "").lower()
               or "update vehicles" in (q or "").lower() for q, _ in update_cursor.executed), "stock UPDATE should be executed"
    assert any("insert into orders" in (q or "").lower() for q, _ in insert_cursor.executed), "orders INSERT should be executed"

    # Verify email sent
    assert len(dummy_smtp.sent) == 1
    _, to_addr, msg = dummy_smtp.sent[0]
    assert to_addr == "int@example.com"
    assert "Online Vehicle Purchase Receipt" in msg


def test_admin_updates_vehicle_then_views_sales_and_get_data(monkeypatch, client):
    """
    Admin updates a vehicle, then requests sales report and get-data endpoints.
    This checks vehicle-inventory POST (UPDATE + commit) and GET endpoints.
    """
    # Prepare cursor for vehicle update (will accept UPDATE)
    vehicle_cursor = SimpleCursor()
    vehicle_conn = SimpleConnection(vehicle_cursor)
    # For get-data and get-order-data, prepare cursors that will return lists
    vehicles_rows = [
        {"vehicleID": 1, "make": "One", "model": "A", "stock": 2, "price": 1000},
        {"vehicleID": 2, "make": "Two", "model": "B", "stock": 0, "price": 2000},
    ]
    vehicles_cursor = SimpleCursor(rows=vehicles_rows)
    vehicles_conn = SimpleConnection(vehicles_cursor)

    orders_rows = [
        {"orderID": 1, "username": "Alice", "vehicle": "One A", "price": 1000, "date": "2025-11-01"}
    ]
    orders_cursor = SimpleCursor(rows=orders_rows)
    orders_conn = SimpleConnection(orders_cursor)

    # Sequence for first POST to vehicle-inventory will use vehicle_conn.
    # Later calls to /get-data and /get-order-data will use vehicles_conn and orders_conn.
    seq = SequenceConnector([vehicle_conn, vehicles_conn, orders_conn])
    monkeypatch.setattr("app.mysql.connector.connect", seq)

    # Set Admin session
    with client.session_transaction() as sess:
        sess["username"] = "Admin"

    # POST to update vehicle
    form = {"name": "Make ModelX", "stock": "5", "price": "15000"}
    resp = client.post("/vehicle-inventory", data=form, follow_redirects=True)
    assert resp.status_code == 200
    # Ensure the update query was executed
    assert any("update vehicles set" in (q or "").lower() for q, _ in vehicle_cursor.executed), "Expected an UPDATE on vehicles"
    assert vehicle_conn.committed, "Expected commit() after vehicle update"

    # Access sales-report (should return template for Admin)
    resp = client.get("/sales-report")
    assert resp.status_code == 200

    # get-data endpoint returns vehicles_rows
    resp = client.get("/get-data")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == len(vehicles_rows)

    # get-order-data returns orders_rows
    resp = client.get("/get-order-data")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == len(orders_rows)


def test_update_payment_and_update_user_flow(monkeypatch, client):
    """
    User updates payment info (mail-form & payment-form) while signed-in,
    then Admin updates a user's profile. This exercises update-payment and update-user routes.
    """
    # For update-payment POSTs, a connection is used for each POST
    mail_cursor = SimpleCursor()
    payment_cursor = SimpleCursor()
    # For update-user (admin POST), another cursor
    update_user_cursor = SimpleCursor()

    mail_conn = SimpleConnection(mail_cursor)
    payment_conn = SimpleConnection(payment_cursor)
    update_user_conn = SimpleConnection(update_user_cursor)

    seq = SequenceConnector([mail_conn, payment_conn, update_user_conn])
    monkeypatch.setattr("app.mysql.connector.connect", seq)

    # 1) update-payment as logged-in user: mail-form
    with client.session_transaction() as sess:
        sess["username"] = "someuser"

    mail_form = {
        "form-identifier": "mail-form",
        "address": "500 Test Ave",
        "address2": "Unit 1",
        "city": "Austin",
        "state": "TX",
        "postal_code": "73301"
    }
    resp = client.post("/update-payment", data=mail_form, follow_redirects=True)
    assert resp.status_code == 200
    # ensure an UPDATE query executed
    assert any("update users set address" in (q or "").lower() for q, _ in mail_cursor.executed)

    # 2) update-payment: payment-form
    payment_form = {
        "form-identifier": "payment-form",
        "name": "First Last",
        "card_number": "4111111111111111",
        "expiration": "12/28",
        "security_code": "321"
    }
    resp = client.post("/update-payment", data=payment_form, follow_redirects=True)
    assert resp.status_code == 200
    assert any("update users set first_name" in (q or "").lower() for q, _ in payment_cursor.executed)

    # 3) update-user as Admin
    with client.session_transaction() as sess:
        sess["username"] = "Admin"

    form = {
        "first-name": "NewFirst",
        "last-name": "NewLast",
        "new-username": "newuser",
        "email": "new@example.com",
        "username": "existing_user"
    }
    resp = client.post("/update-user", data=form, follow_redirects=True)
    assert resp.status_code == 200
    assert any("update users set first_name" in (q or "").lower() or "update users set first_name" in (q or "") for q, _ in update_user_cursor.executed)


def test_get_user_data_json_and_get_with_session(monkeypatch, client):
    """
    Tests /get-user-data both with JSON payload (targeting arbitrary username)
    and without JSON (returns data for session user).
    """
    # Prepare DB cursor for POST (JSON) request: return a dict-like row
    user_row = [{"username": "other_user", "email": "other@example.com"}]
    post_cursor = SimpleCursor(rows=user_row)
    get_cursor = SimpleCursor(rows=[{"username": "session_user", "email": "session@example.com"}])

    post_conn = SimpleConnection(post_cursor)
    get_conn = SimpleConnection(get_cursor)

    seq = SequenceConnector([post_conn, get_conn])
    monkeypatch.setattr("app.mysql.connector.connect", seq)

    # POST JSON to get other user's data
    payload = {"username": "other_user"}
    resp = client.post("/get-user-data", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert data[0]["username"] == "other_user"

    # Now set session username and GET (no JSON)
    with client.session_transaction() as sess:
        sess["username"] = "session_user"

    resp = client.get("/get-user-data")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert data[0]["username"] == "session_user"
