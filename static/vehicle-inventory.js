let vehicleData = [];

const vehicleContainer = document.getElementById('vehicle-form');

window.addEventListener('load', async () => {
    const res = await fetch('/get-user-data');
    vehicleData = await res.json();
    renderVehicleInventory();
});

function renderVehicleInventory() {
    // set vehicle form
    vehicleContainer.innerHTML = `<input type="hidden" name="form-identifier" value="mail-form">

        <label for="address">Street Address</label><br>
        <input type="text" id="address" name="address" value=${vehicleData[0].address}><br><br>

        <label for="address2">Apt., Suite, Etc.</label><br>
        <input type="text" id="address2" name="address2" value=${vehicleData[0].address2}><br><br>

        <label for="city">City</label><br>
        <input type="text" id="city" name="city" value=${vehicleData[0].city}><br><br>

        <label for="state">State/Province</label><br>
        <input type="text" id="state" name="state" value=${vehicleData[0].state}><br><br>

        <label for="postal_code">Postal/Zip Code</label><br>
        <input type="text" id="postal_code" name="postal_code" value=${vehicleData[0].postal_code}><br><br>

        <input type="submit" value="Save Info">`;
        //temp
        `<label for="name">Name</label><br>
        <input type="text" id="name" name="name"><br><br>

        <label for="stock">Stock</label><br>
        <input type="text" id="stock" name="stock"><br><br>

        <label for="price">Price</label><br>
        <input type="text" id="price" name="price"><br><br>

        <input type="submit" value="Update">`;
}

