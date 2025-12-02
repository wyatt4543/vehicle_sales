# tests/test_index.py
import sys
import os
import json
import types
import pytest

# make sure we can import app from project root (same pattern as your other tests)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

# Reuse client fixture pattern from your other test file
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'testkey'
    return app.test_client()

# --- Fake DB helpers -------------------------------------------------------
class FakeCursor:
    def __init__(self, rows):
        # rows should be a list (for dictionary=True)
        self._rows = rows

    def execute(self, *args, **kwargs):
        # no-op; included for compatibility
        pass

    def fetchall(self):
        return self._rows

    def close(self):
        pass

class FakeConnection:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, dictionary=True, buffered=True):
        return FakeCursor(self._rows)

    def close(self):
        pass

    def is_connected(self):
        return True

# --- Tests ---------------------------------------------------------------
def test_index_page_contains_catalog_container_and_script(client):
    """Index page should render and include the catalog container + main.js script tag."""
    resp = client.get('/')
    assert resp.status_code == 200

    html = resp.data.decode()
    # Basic sanity checks for the page structure required by the UI/JS
    assert '<div class="catalog-flex" id="catalog-container">' in html
    assert "List Of Vehicles" in html
    # Ensure the main.js script is referenced
    assert "main.js" in html

def test_get_data_returns_vehicles_in_ascending_vehicleID_order(monkeypatch, client):
    """
    TC-1 (positive): If the database returns vehicle rows in ascending vehicleID order,
    the /get-data endpoint should return that list (the front-end will render using that order).
    """

    # Prepare fake DB rows (already in correct ascending vehicleID order)
    fake_rows = [
        {'vehicleID': 1, 'make': 'Alpha', 'model': 'One', 'stock': 5, 'price': 10000},
        {'vehicleID': 2, 'make': 'Beta',  'model': 'Two', 'stock': 3, 'price': 12000},
        {'vehicleID': 3, 'make': 'Gamma', 'model': 'Three', 'stock': 1, 'price': 15000},
    ]

    # monkeypatch the mysql connector used by app (app.py imported mysql.connector at top-level)
    def fake_connect(**kwargs):
        return FakeConnection(fake_rows)

    monkeypatch.setattr('app.mysql.connector.connect', fake_connect)

    resp = client.get('/get-data')
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    # Ensure the returned list order has ascending vehicleID values
    ids = [int(item['vehicleID']) for item in data]
    assert ids == sorted(ids), f"vehicleIDs must be ascending, got {ids}"

    # Sanity check that the returned items contain expected fields
    for item in data:
        assert 'make' in item and 'model' in item and 'price' in item

def test_get_data_handles_database_error_gracefully(monkeypatch, client):
    import mysql.connector

    class DummyDBError(mysql.connector.Error):
        pass

    def raising_connect(**kwargs):
        raise DummyDBError("simulated database connection failure")

    monkeypatch.setattr('app.mysql.connector.connect', raising_connect)

    resp = client.get('/get-data')
    assert resp.status_code == 200

    data = resp.get_json()
    assert 'error' in data
    assert "simulated database connection failure" in data['error']
