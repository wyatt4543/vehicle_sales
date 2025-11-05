let vehicleData = [];
let filteredData = []; // For storing filtered data

const container = document.getElementById('catalog-container');
const searchInput = document.getElementById('search-input');
const sortBySelect = document.getElementById('sort-by');

window.addEventListener('load', async () => {
    const res = await fetch('/get-data');
    vehicleData = await res.json();
    filteredData = vehicleData;
    renderProducts(filteredData.length);
});

function renderProducts(number) {
    container.innerHTML = ''; // Clear existing items
    for (i = 0; i < number; i++) {
        const item = document.createElement('div');
        item.classList.add('catalog-item');
        item.innerHTML = `<h2>${filteredData[i].make} ${filteredData[i].model}</h2>
        <div class="vehicle-stats"><p class="vehicle-price"> Price: $${filteredData[i].price.toLocaleString()}</p>
        <p class="vehicle-stock"> Stock: ${filteredData[i].stock}</p></div>
        <img src="/static/Vehicle Images/IMG${String(filteredData[i].vehicleID).padStart(3, '0')}.png" alt="${filteredData[i].make} ${filteredData[i].model}">
        <button onclick="transferPurchase(${i})" type="button" id="purchase">Purchase</button>`;
        container.appendChild(item);
    };
}

function applyFilters() {
    const sortValue = sortBySelect.value;

    filteredData = [...vehicleData];

    // Sort the filtered data
    switch (sortValue) {
        case 'price_desc':
            filteredData.sort((a, b) => b.price - a.price);
            break;
        case 'price_asc':
            filteredData.sort((a, b) => a.price - b.price);
            break;
        case 'model_asc':
            filteredData.sort((a, b) => a.model.localeCompare(b.model));
            break;
        case 'make_asc':
            filteredData.sort((a, b) => a.make.localeCompare(b.make));
            break;
        case 'none':
            filteredData.sort((a, b) => a.vehicleID - b.vehicleID);
            break;
        default:
            filteredData.sort((a, b) => a.vehicleID - b.vehicleID);
            break;
    }

    // Render the newly filtered and sorted data
    renderProducts(filteredData.length);
}

function applySearch() {
    const searchText = (searchInput.value || '').trim().toLowerCase();

    if (searchText === '') {
        // show full list if no search text
        filteredData = [...vehicleData];
        filteredData.sort((a, b) => a.vehicleID - b.vehicleID);
        renderProducts(vehicleData.length);
        return;
    }

    // Filter the data based on search input
    filteredData = vehicleData.filter(vehicle => {
        const searchString = `${vehicle.make} ${vehicle.model}`;
        return searchString.toLowerCase().includes(searchText);
    });

    // Render the newly filtered and sorted data
    renderProducts(filteredData.length);
}

function transferPurchase(i) {
    localStorage.setItem('make', filteredData[i].make);
    localStorage.setItem('model', filteredData[i].model);
    localStorage.setItem('price', filteredData[i].price.toLocaleString());
    localStorage.setItem('vehicleID', String(filteredData[i].vehicleID).padStart(3, '0'))
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

