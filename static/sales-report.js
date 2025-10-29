let orderData = [];

const container = document.getElementById('catalog-container');

window.addEventListener('load', async () => {
    const res = await fetch('/get-order-data');
    orderData = await res.json();
    renderOrders(orderData.length);
});

function renderOrders(number) {
    container.innerHTML = ''; // Clear existing orders
    for (i = 0; i < number; i++) {
        const order = document.createElement('tr');
        order.classList.add('order-row');
        order.innerHTML = `<td>${orderData[i].vehicle}</td>
                           <td>${orderData[i].price}</td>
                           <td>1</td>
                           <td>${orderData[i].date}</td>`
        container.appendChild(order);
    };
}

