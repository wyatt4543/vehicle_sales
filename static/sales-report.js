// written by: Wyatt McDonnell
// tested by: Wyatt McDonnell
// debugged by: Wyatt McDonnell

let orderData = [];

const container = document.getElementById('orders-container');

window.addEventListener('load', async () => {
    const res = await fetch('/get-order-data');
    orderData = await res.json();
    renderOrders(orderData.length);
});

function renderOrders(number) {
    container.innerHTML = '<tr><th>Vehicle</th><th>Price</th><th>Quantity</th><th>Date</th></tr>'; // Clear existing orders
    for (i = 0; i < number; i++) {
        //remove the hours and minutes from each date
        orderData[i].date = orderData[i].date.split('00:')[0];
        const order = document.createElement('tr');
        order.classList.add('order-row');
        order.innerHTML = `<td>${orderData[i].vehicle}</td>
                           <td>${orderData[i].price}</td>
                           <td>1</td>
                           <td>${orderData[i].date}</td>`;
        container.appendChild(order);
    };
}

