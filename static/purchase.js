// written by: Wyatt McDonnell & Mamadou Oumar Ndiaye
// tested by: Wyatt McDonnell
// debugged by: Wyatt McDonnell

let make = localStorage.getItem('make');
let model = localStorage.getItem('model');
let price = localStorage.getItem('price');
let vehicleID = localStorage.getItem('vehicleID');

let vehicleName = document.getElementById('vehicle-name');
vehicleName.innerHTML = `${make} ${model}`;

let vehicleImage = document.getElementById('vehicle-image');
vehicleImage.src = `/static/Vehicle Images/IMG${vehicleID}.png`;
vehicleImage.alt = `${make} ${model}`;

let vehiclePrice = document.getElementById('total-amount');
vehiclePrice.innerHTML = `$${price}`;

document.getElementById("confirmButton").addEventListener("click", async function () {
    // Gather form elements
    const address = document.getElementById("address").value.trim();
    const address2 = document.getElementById("address2").value.trim();
    const city = document.getElementById("city").value.trim();
    const state = document.getElementById("state").value.trim();
    const zip = document.getElementById("zip").value.trim();

    const cardName = document.getElementById("cardName").value.trim();
    const cardNumber = document.getElementById("cardNumber").value.trim();
    const expDate = document.getElementById("expDate").value;
    const cvv = document.getElementById("cvv").value.trim();

    const emailPurchase = document.getElementById("emailPurchaseInfo").checked;

    const deliveryOption = document.querySelector('input[name="deliveryOption"]:checked');
    const saveInfo = document.getElementById("saveInfo").checked;

    // Basic validation
    if (!address || !city || !state || !zip ||
        !cardName || !cardNumber || !expDate || !cvv) {
        alert("⚠️ Please fill out all required fields before confirming your purchase.");
        return;
    }

    if (!deliveryOption) {
        alert("⚠️ Please select a delivery option.");
        return;
    }

    // Basic format check for card number and CVV
    const cardNumPattern = /^\d{16}$/; // 16 digits
    const cvvPattern = /^\d{3,4}$/;    // 3 or 4 digits

    if (!cardNumPattern.test(cardNumber)) {
        alert("⚠️ Invalid card number. Please enter a 16-digit number.");
        return;
    }

    if (!cvvPattern.test(cvv)) {
        alert("⚠️ Invalid CVV. Please enter 3 or 4 digits.");
        return;
    }

    // Check if the card number is a valid number
    function checkLuhn(cardNumber) {
        let nDigits = cardNumber.length;

        let nSum = 0;
        let isSecond = false;
        for (let i = nDigits - 1; i >= 0; i--) {

            let d = cardNumber[i].charCodeAt() - '0'.charCodeAt();

            if (isSecond == true)
                d = d * 2;

            // We add two digits to handle
            // cases that make two digits
            // after doubling
            nSum += parseInt(d / 10, 10);
            nSum += d % 10;

            isSecond = !isSecond;
        }
        return (nSum % 10 == 0);
    }

    if (!checkLuhn(cardNumber)) {
        alert("⚠️ Invalid card number. Please a real card number.");
        return;
    }

    // Check if the user's name matches with the information in the database
    const res = await fetch('/get-user-data');
    userData = await res.json();
    storedName = `${userData[0].first_name} ${userData[0].last_name}`

    if (cardName != storedName) {
        alert("⚠️ Invalid name. Please your real name.");
        return;
    }

    // If validation passes
    let message = `✅ Purchase confirmed!\n\nThank you, ${cardName}!\nYour vehicle will be ${deliveryOption.value === "in-store" ? "ready for pickup in-store" : "delivered to your address"
        }.`;

    if (saveInfo) {
        message += "\n\n💾 Your information has been saved for future purchases.";

        // Store the purchase information in a constant
        const purchaseInfo = {
            address: address,
            address2: address2,
            city: city,
            state: state,
            zip: zip,
            cardNumber: cardNumber,
            expDate: expDate,
            cvv: cvv,
        };

        // Save payment & mailing information to the database
        fetch('/save-purchase-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json' // Important for JSON data
            },
            body: JSON.stringify(purchaseInfo) // Convert JavaScript object to JSON string
        });
    }

    // Make it -1 to signify no pick up in-store
    let generatedCode = -1

    // Only generate a random code if the vehicle is being picked up in-store
    if (deliveryOption.value === "in-store") {
        generatedCode = Math.floor(1000 + Math.random() * 9000);
        message += `\n\nThe pick-up code for your vehicle is: ${generatedCode}`;
    }

    alert(message);

    // Data being sent after purchase
    const purchaseData = {
        vehicleID: parseInt(vehicleID),
        emailPurchase: emailPurchase,
        customer: cardName,
        vehicleName: make + " " + model,
        vehiclePrice: price,
        deliveryCode: generatedCode,
    };

    // Send the data
    fetch('/purchase-info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json' // Important for JSON data
        },
        body: JSON.stringify(purchaseData) // Convert JavaScript object to JSON string
    })
    .then(response => {
        // Check if the server responded successfully (status 200-299)
        if (!response.ok) {
            // Throw an error if the server returned a 4xx or 5xx status
            throw new Error('Server error: ' + response.statusText);
        }

        window.location.href = '/'; // Redirect to your desired success page
    });
});