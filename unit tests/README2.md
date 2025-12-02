# Unit Testing for  `purchase` Page

This testing script uses `pytest` to verify the functionality of the `/purchase` page in a Flask web application. It ensures the page works correctly and displays the expected content when a user is logged in.

## Setup

* The script adds the parent directory to `sys.path` so it can import the Flask app.
* The `pytest` framework is used for running the tests.

## Fixtures

1. **`client`**

   * Creates a test version of the Flask app.
   * Enables testing mode (`TESTING=True`) for accurate test behavior.
   * Sets a secret key for session handling.
   * Returns a Flask test client to simulate requests.

2. **`logged_in_client`**

   * Uses the `client` fixture.
   * Simulates a logged-in user by adding a fake `username` to the session.
   * Required because the `/purchase` page needs an authenticated user.

## Tests

1. **`test_purchase_page_status_code`**

   * Sends a GET request to `/purchase` with a logged-in client.
   * Checks that the server responds with a `200 OK` status, meaning the page loads successfully.

2. **`test_purchase_page_contains_required_text`**

   * Sends a GET request to `/purchase` with a logged-in client.
   * Converts the HTML response from bytes to a string.
   * Verifies that the page contains key sections, including:

     * "Purchase"
     * "VEHICLE NAME"
     * "Mail Information"
     * "Payment Information"
     * "Delivery Options"
     * "Confirm Purchase"

These checks ensure the main elements of the purchase page are present and visible to the user.

