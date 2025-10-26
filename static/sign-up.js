function validatePassword() {
    var password = document.getElementById("password").value;
    var confirmPassword = document.getElementById("confirm-pass").value;

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return false; // Prevent form submission
    }
    return true; // Allow form submission
}