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

document.getElementById("confirmButton").addEventListener("click", function () {
    // Gather form elements
    const name = document.getElementById("name").value.trim();
    const address = document.getElementById("address").value.trim();
    const city = document.getElementById("city").value.trim();
    const state = document.getElementById("state").value.trim();
    const zip = document.getElementById("zip").value.trim();

    const cardName = document.getElementById("cardName").value.trim();
    const cardNumber = document.getElementById("cardNumber").value.trim();
    const expDate = document.getElementById("expDate").value;
    const cvv = document.getElementById("cvv").value.trim();

    const deliveryOption = document.querySelector('input[name="deliveryOption"]:checked');
    const saveInfo = document.getElementById("saveInfo").checked;

    // Basic validation
    if (!name || !address || !city || !state || !zip ||
        !cardName || !cardNumber || !expDate || !cvv) {
        alert("⚠️ Please fill out all required fields before confirming your purchase.");
        return;
    }

    if (!deliveryOption) {
        alert("⚠️ Please select a delivery option.");
        return;
    }

    // Optional: Basic format check for card number and CVV
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

    // If validation passes
    let message = `✅ Purchase confirmed!\n\nThank you, ${name}!\nYour vehicle will be ${deliveryOption.value === "in-store" ? "ready for pickup in-store" : "delivered to your address"
        }.\n\n`;

    if (saveInfo) {
        message += "💾 Your information has been saved for future purchases.";
        // Example localStorage save (for demo)
        localStorage.setItem("savedUserInfo", JSON.stringify({
            name, address, city, state, zip, cardName
        }));
    }

    alert(message);

    // Optionally clear forms
    document.getElementById("mailForm").reset();
    document.getElementById("paymentForm").reset();
    document.getElementById("deliveryForm").reset();
    document.getElementById("saveInfo").checked = false;
});