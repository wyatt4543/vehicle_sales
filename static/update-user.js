let userData = [];

const container = document.getElementById('user-form');

async function getUser() {
    const res = await fetch('/get-user-data');
    userData = await res.json();
    renderUserInfo();
};

function renderUserInfo() {
    // change the form for new information submission
    myForm.removeAttribute("onsubmit");
    myForm.setAttribute("action", "/update-user");
    myForm.setAttribute("method", "post");

    container.innerHTML = `<label for="username">Username</label><br>
        <input type="text" id="username" name="username"><br><br>

        <label for="stock">Stock</label><br>
        <input type="text" id="stock" name="stock"><br><br>

        <label for="price">Price</label><br>
        <input type="text" id="price" name="price"><br><br>

        <input type="submit" value="Update">`;
}

