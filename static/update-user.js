let userData = [];

const container = document.getElementById('user-form');
const userElement = document.getElementById('username');

async function getUser() {
    const res = await fetch('/get-user-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: userElement.value })
    });
    userData = await res.json();
    renderUserInfo();
};

function renderUserInfo() {
    // change the form for new information submission
    container.removeAttribute("onsubmit")
    container.setAttribute("action", "/update-user");
    container.setAttribute("method", "post");

    container.innerHTML = `<label for="first-name">First Name</label><br>
        <input type="text" id="first-name" name="first-name" value=${userData[0].first_name}><br><br>

        <label for="last-name">Last Name</label><br>
        <input type="text" id="last-name" name="last-name" value=${userData[0].last_name}><br><br>

        <label for="username">Username</label><br>
        <input type="text" id="username" name="username" value=${userData[0].username}><br><br>

        <label for="email">Email</label><br>
        <input type="email" id="email" name="email" value=${userData[0].email}><br><br>

        <input type="submit" value="Update">`;
}

