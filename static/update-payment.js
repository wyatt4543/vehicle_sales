let paymentMailData = [];

const mailContainer = document.getElementById('mail-form');
const paymentContainer = document.getElementById('payment-form');

window.addEventListener('load', async () => {
    const res = await fetch('/get-user-data');
    paymentMailData = await res.json();
    renderPaymentMailInfo();
});

function renderPaymentMailInfo() {
    // set mail form
    mailContainer.innerHTML = `<input type="hidden" name="form-identifier" value="mail-form">

        <label for="address">Street Address</label><br>
        <input type="text" id="address" name="address" value=${paymentMailData[0]}><br><br>

        <label for="address2">Apt., Suite, Etc.</label><br>
        <input type="text" id="address2" name="address2" value=${paymentMailData[0]}><br><br>

        <label for="city">City</label><br>
        <input type="text" id="city" name="city" value=${paymentMailData[0]}><br><br>

        <label for="state">State/Province</label><br>
        <input type="text" id="state" name="state" value=${paymentMailData[0]}><br><br>

        <label for="postal_code">Postal/Zip Code</label><br>
        <input type="text" id="postal_code" name="postal_code" value=${paymentMailData[0]}><br><br>

        <input type="submit" value="Save Info">`;

    // set payment form
    paymentContainer.innerHTML = `<input type="hidden" name="form-identifier" value="payment-form">

        <label for="name">Card Holder Name</label><br>
        <input type="text" id="name" name="name" value=${paymentMailData[0]}><br><br>

        <label for="card_number">Card Number</label><br>
        <input type="text" id="card_number" name="card_number" value=${paymentMailData[0]}><br><br>

        <label for="expiration">Expiration Date</label><br>
        <input type="text" id="expiration" name="expiration" value=${paymentMailData[0]}><br><br>

        <label for="security_code">Security Code</label><br>
        <input type="text" id="security_code" name="security_code" value=${paymentMailData[0]}><br><br>

        <input type="submit" value="Save Info">`;
}

