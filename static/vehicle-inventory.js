// written by: Wyatt McDonnell
// tested by: Wyatt McDonnell
// debugged by: Wyatt McDonnell

let vehicleData = [];

const vehicleContainer = document.getElementById('vehicle-form');

window.addEventListener('load', async () => {
    const res = await fetch('/get-data');
    vehicleData = await res.json();
    renderVehicleInventory();
});

function renderVehicleInventory() {
    // load form after data recieved
    vehicleContainer.innerHTML = `<label for="name">Name:</label><br>
        <select id="name" name="name" onchange="updateDetails()"></select><br><br>

        <label for="stock">Stock:</label><br>
        <input type="text" id="stock" name="stock"><br><br>

        <label for="price">Price:</label><br>
        <input type="text" id="price" name="price"><br><br>

        <input type="submit" value="Update">`

    // get the vehicle dropdown
    const selectElement = document.getElementById('name');

    // Loop through the Data array and populate the dropdown
    vehicleData.forEach(vehicle => {
        // Create a new <option> element
        const option = document.createElement('option');

        // Set the text of the option by combining the make and model
        option.textContent = `${vehicle.make} ${vehicle.model}`;

        // Set the value of the option
        option.value = `${vehicle.make} ${vehicle.model}`;

        // Append the option to the select element
        selectElement.appendChild(option);
    });

    // fill in intial vehicle values
    updateDetails();
}

// Function to update the stock and price fields
function updateDetails() {
    // get the vehicle dropdown
    const selectElement = document.getElementById('name'); 

    // Get the selected combined make and model string
    const selectedMakeModel = selectElement.value;

    // Find the corresponding vehicle object in the data
    const selectedVehicle = vehicleData.find(vehicle =>
        `${vehicle.make} ${vehicle.model}` === selectedMakeModel
    );

    // Get the stock and price input fields
    const stockInput = document.getElementById('stock');
    const priceInput = document.getElementById('price');

    if (selectedVehicle) {
        // Update the input fields with the new data
        stockInput.value = selectedVehicle.stock;
        priceInput.value = selectedVehicle.price;
    }
}

function dropDown() {
    const dropdownContent = document.getElementById('dropdownContent');
    if (dropdownContent.style.visibility === 'hidden') {
        dropdownContent.style.visibility = 'visible';
    } else {
        dropdownContent.style.visibility = 'hidden';
    }
}
