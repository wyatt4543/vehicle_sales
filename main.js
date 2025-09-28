let number = 4;

const container = document.getElementById('catalog-container');

function renderProducts(number) {
    container.innerHTML = ''; // Clear existing items
    for (i = 0; i < number; i++) {
        const item = document.createElement('div');
        item.classList.add('catalog-item');
        item.innerHTML = `<h2>Toyota Camry</h2><p> Stock: 10 Price: $25, 657</p><img src="Vehicle Images/IMG${String(i + 1).padStart(3, '0')}.png" alt="White Toyota Camry" width="500" height="250"><button onclick="location.href='purchase.html'" type="button">Purchase</button>`
        container.appendChild(item);
    };
}

renderProducts(number);