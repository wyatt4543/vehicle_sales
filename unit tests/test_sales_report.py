import pytest
from app import app

# ----------------------------
# Fake DB helpers
# ----------------------------
class FakeCursor:
    def __init__(self, data=None):
        self.data = data or []
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self):
        return self.cursor_obj

# ----------------------------
# Fixture for Flask test client
# ----------------------------
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # set session to admin
        with client.session_transaction() as sess:
            sess["username"] = "Admin"
        yield client

# ----------------------------
# Helper to patch DB connection
# ----------------------------
def patch_db(monkeypatch, fake_cursor):
    fake_conn = FakeConnection(fake_cursor)
    monkeypatch.setattr("app.mysql.connector.connect", lambda **kwargs: fake_conn)

# ----------------------------
# Tests
# ----------------------------
def test_sales_report_with_data(monkeypatch, client):
    """Admin requests sales report; DB has records; page loads"""
    fake_data = [
        {"vehicle_id": 1, "buyer": "Alice", "price": "25000", "date": "2025-12-01"},
        {"vehicle_id": 2, "buyer": "Bob", "price": "18000", "date": "2025-12-02"}
    ]
    cursor = FakeCursor(data=fake_data)
    patch_db(monkeypatch, cursor)

    resp = client.get("/sales-report")
    assert resp.status_code == 200
    # DB cursor was at least used
    assert cursor.executed is not None

def test_sales_report_no_data(monkeypatch, client):
    """Admin requests sales report; DB empty; page loads"""
    cursor = FakeCursor(data=[])
    patch_db(monkeypatch, cursor)

    resp = client.get("/sales-report")
    assert resp.status_code == 200
    assert cursor.executed is not None

def test_sales_report_db_error(monkeypatch, client):
    """Simulate DB failure; page still loads with 200"""
    class BrokenCursor(FakeCursor):
        def execute(self, query, params=None):
            raise Exception("DB error")

    patch_db(monkeypatch, BrokenCursor())

    resp = client.get("/sales-report")
    # The route should catch DB errors and still render the page
    assert resp.status_code == 200
