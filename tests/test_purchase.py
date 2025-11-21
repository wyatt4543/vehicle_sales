import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
import pytest

# Creates a test version of the Flask app
@pytest.fixture
def client():
    app.config['TESTING'] = True            # Enable testing mode
    app.config['SECRET_KEY'] = 'testkey'    # Required for session handling
    return app.test_client()                # Return Flask test client

# Simulates a logged-in user (the /purchase page requires login)
@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'       # Fake user in session
    return client

# Test: The purchase page should load successfully
def test_purchase_page_status_code(logged_in_client):
    response = logged_in_client.get('/purchase')
    assert response.status_code == 200      # Expect OK status

# Test: The purchase page should contain key sections from the HTML
def test_purchase_page_contains_required_text(logged_in_client):
    response = logged_in_client.get('/purchase')
    html = response.data.decode()           # Convert bytes → string

    # Check for important page elements
    assert "Purchase" in html
    assert "VEHICLE NAME" in html
    assert "Mail Information" in html
    assert "Payment Information" in html
    assert "Delivery Options" in html
    assert "Confirm Purchase" in html
