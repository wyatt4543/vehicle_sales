let vehicleData = [];

const container = document.getElementById('catalog-container');

window.addEventListener('load', async () => {
    const res = await fetch('/get-data');
    vehicleData = await res.json();
    console.log(vehicleData);
    console.log(vehicleData[1]);
    renderProducts(vehicleData.length);
});

function renderProducts(number) {
    container.innerHTML = ''; // Clear existing items
    for (i = 0; i < number; i++) {
        const item = document.createElement('div');
        item.classList.add('catalog-item');
        item.innerHTML = `<h2>${vehicleData[i].make} ${vehicleData[i].model}</h2>
        <p> Stock: ${vehicleData[i].stock} Price: $${vehicleData[i].price.toLocaleString()}</p>
        <img src="/static/Vehicle Images/IMG${String(i + 1).padStart(3, '0')}.png" alt="${vehicleData[i].make} ${vehicleData[i].model}">
        <button onclick="location.href='/purchase'" type="button">Purchase</button>`
        container.appendChild(item);
    };
}

