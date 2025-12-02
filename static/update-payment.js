// written by: Wyatt McDonnell
// tested by: Wyatt McDonnell
// debugged by: Wyatt McDonnell

let paymentMailData = [];

const mailContainer = document.getElementById('mail-form');
const paymentContainer = document.getElementById('payment-form');

window.addEventListener('load', async () => {
    const res = await fetch('/get-user-data');
    paymentMailData = await res.json();
    renderPaymentMailInfo();
});

function getValue(value) {
    if (value === undefined || value === null) {
        return '';
    }
    return value;
}

function renderPaymentMailInfo() {
    // set mail form
    mailContainer.innerHTML = `<input type="hidden" name="form-identifier" value="mail-form">

        <label for="address">Street Address</label><br>
        <input type="text" id="address" name="address" value="${getValue(paymentMailData[0].address)}"><br><br>

        <label for="address2">Apt., Suite, Etc.</label><br>
        <input type="text" id="address2" name="address2" value="${getValue(paymentMailData[0].address2)}"><br><br>

        <label for="city">City</label><br>
        <input type="text" id="city" name="city" value=${getValue(paymentMailData[0].city)}><br><br>

        <label for="state">State/Province</label><br>
        <input type="text" id="state" name="state" value=${getValue(paymentMailData[0].state)}><br><br>

        <label for="postal_code">Postal/Zip Code</label><br>
        <input type="text" id="postal_code" name="postal_code" value=${getValue(paymentMailData[0].postal_code)}><br><br>

        <div class="save-button">
        <input type="submit" value="Save Info">
        </div>`;

    // set payment form
    paymentContainer.innerHTML = `<input type="hidden" name="form-identifier" value="payment-form">

        <label for="name">Card Holder Name</label><br>
        <input type="text" id="name" name="name" value="${getValue(paymentMailData[0].first_name)} ${getValue(paymentMailData[0].last_name)}"><br><br>

        <label for="card_number">Card Number</label><br>
        <input type="text" id="card_number" name="card_number" value=${getValue(paymentMailData[0].card_number)}><br><br>

        <label for="expiration">Expiration Date</label><br>
        <input type="text" id="expiration" name="expiration" value="${getValue(paymentMailData[0].expiration)}"><br><br>

        <label for="security_code">Security Code</label><br>
        <input type="text" id="security_code" name="security_code" value=${getValue(paymentMailData[0].security_code)}><br><br>

        <div class="save-button">
        <input type="submit" value="Save Info">
        </div>`;
}

