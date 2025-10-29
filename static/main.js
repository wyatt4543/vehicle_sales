let vehicleData = [];

const container = document.getElementById('catalog-container');

window.addEventListener('load', async () => {
    const res = await fetch('/get-data');
    vehicleData = await res.json();
    renderProducts(vehicleData.length);
});

function renderProducts(number) {
    container.innerHTML = ''; // Clear existing items
    for (i = 0; i < number; i++) {
        const item = document.createElement('div');
        item.classList.add('catalog-item');
        item.innerHTML = `<h2>${vehicleData[i].make} ${vehicleData[i].model}</h2>
        <p> Stock: ${vehicleData[i].stock} Price: $${vehicleData[i].price.toLocaleString()}</p>
        <img src="/static/Vehicle Images/IMG${String(vehicleData[i].vehicleID).padStart(3, '0')}.png" alt="${vehicleData[i].make} ${vehicleData[i].model}">
        <button onclick="transferPurchase(${i})" type="button" id="purchase">Purchase</button>`;
        container.appendChild(item);
    };
}

function transferPurchase(i) {
    localStorage.setItem('make', vehicleData[i].make);
    localStorage.setItem('model', vehicleData[i].model);
    localStorage.setItem('price', vehicleData[i].price.toLocaleString());
    localStorage.setItem('vehicleID', String(vehicleData[i].vehicleID).padStart(3, '0'))
    window.location.href = '/purchase';
}

function dropDown() {
    const dropdownContent = document.getElementById('dropdownContent');
    if (dropdownContent.style.visibility === 'hidden') {
        dropdownContent.style.visibility = 'visible';
    } else {
        dropdownContent.style.visibility = 'hidden';
    }
}

