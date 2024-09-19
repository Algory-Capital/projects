var isAuthenticated = false;

function authenticate() {
    const passwordInput = document.getElementById('password');
    const passwordLabel = document.getElementById('passwordlabel');
    const passwordDiv = document.getElementById('passworddiv');

    const loginForm = document.getElementById('loginForm');
    const originalContent = document.getElementById('originalContent');

    const enteredPassword = passwordInput.value.trim();
    const correctPassword = "AlgoryMogs"; // please do not steal this :) i was too lazy to do server-side auth

    if (enteredPassword === correctPassword) {
        loginForm.style.opacity = '0'; // Hide the login form
        loginForm.style.zIndex = '-1';
        originalContent.style.opacity = '1'; // Show the original content
        isAuthenticated = true;
    } else {
        passwordInput.value = "";
        passwordLabel.classList.remove('persist');
        passwordDiv.classList.remove('persist');
        alert('Incorrect password. Please try again.');
    }
};