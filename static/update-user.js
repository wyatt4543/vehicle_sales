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
        const order = document.createElement('tr');
        order.classList.add('order-row');
        order.innerHTML = `<label for="username">Username</label><br>
        <input type="text" id="username" name="username"><br><br>

        <label for="stock">Stock</label><br>
        <input type="text" id="stock" name="stock"><br><br>

        <label for="price">Price</label><br>
        <input type="text" id="price" name="price"><br><br>

        <input type="submit" value="Update">`
        container.appendChild(order);
    };
}

