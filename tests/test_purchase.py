import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


# Helper for valid purchase form data
def valid_data(extra=None):
    data = {
        "address": "123 Road St",
        "city": "Cityville",
        "state": "TX",
        "zip": "77777",
        "phone": "1234567890",
        "card-number": "4111111111111111",
        "card-exp": "12/30",
        "card-cvv": "123",
        "delivery-method": "delivery",
        "receipt-mail": "yes",
        "receipt-email": "yes",
    }
    if extra:
        data.update(extra)
    return data


# ------------------------------------------------------------
# 1. Valid info – delivery, mail+email receipts
# ------------------------------------------------------------
def test_purchase_delivery_mail_email_success(client):
    response = client.post("/purchase", data=valid_data(), follow_redirects=True)

    assert response.status_code == 200
    assert b"Success" in response.data
    assert b"receipt" in response.data
    assert b"email" in response.data
    assert b"mail" in response.data


# ------------------------------------------------------------
# 2. Valid info – delivery only (no receipts)
# ------------------------------------------------------------
def test_purchase_delivery_only_success(client):
    data = valid_data({
        "receipt-mail": "",
        "receipt-email": ""
    })
    response = client.post("/purchase", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Success" in response.data
    assert b"pickup code" not in response.data


# ------------------------------------------------------------
# 3. Valid info – pickup, mail + email receipt
# ------------------------------------------------------------
def test_purchase_pickup_mail_email_success(client):
    data = valid_data({
        "delivery-method": "pickup"
    })
    response = client.post("/purchase", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Success" in response.data
    assert b"pickup code" in response.data
    assert b"mail" in response.data
    assert b"email" in response.data


# ------------------------------------------------------------
# 4. Valid info – pickup only
# ------------------------------------------------------------
def test_purchase_pickup_only_success(client):
    data = valid_data({
        "delivery-method": "pickup",
        "receipt-mail": "",
        "receipt-email": ""
    })
    response = client.post("/purchase", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert b"Success" in response.data
    assert b"pickup code" in response.data


# ------------------------------------------------------------
# 5. Invalid info → user warned
# ------------------------------------------------------------
def test_purchase_invalid_info_failure(client):
    invalid_data = {
        "address": "### BAD ###",
        "city": "?",
        "state": "1!",
        "zip": "abcde",
        "phone": "notaphone",
        "card-number": "bad",
        "card-exp": "99/99",
        "card-cvv": "xx",
        "delivery-method": "delivery",
        "receipt-mail": "yes",
        "receipt-email": "yes",
    }

    response = client.post("/purchase", data=invalid_data, follow_redirects=True)

    # Look for error-related wording
    assert (
        b"invalid" in response.data
        or b"Invalid" in response.data
        or b"error" in response.data
    )
    assert response.status_code == 200
