const API_URL = "https://number-lookup-api.onrender.com";


// ============================================================
// ELEMENTS
// ============================================================

const loginPanel = document.getElementById("loginPanel");
const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("loginButton");
const loginMessage = document.getElementById("loginMessage");

const lookupPanel = document.getElementById("lookupPanel");

const databaseInput = document.getElementById("database");
const numberInput = document.getElementById("number");

const runButton = document.getElementById("runButton");
const logoutButton = document.getElementById("logoutButton");

const responseBox = document.getElementById("response");


// ============================================================
// INITIAL SESSION CHECK
// ============================================================

document.addEventListener("DOMContentLoaded", async () => {
    await checkSession();
});


// ============================================================
// CHECK SESSION
// ============================================================

async function checkSession() {

    try {

        const response = await fetch(
            API_URL + "/api/session",
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data = await response.json();

        if (data.authenticated === true) {
            showAuthenticated();
        } else {
            showLogin();
        }

    } catch (error) {

        showLogin();

        loginMessage.textContent =
            "Unable to connect to authentication server.";

    }
}


// ============================================================
// LOGIN
// ============================================================

async function login() {

    const password = passwordInput.value.trim();

    if (!password) {

        loginMessage.textContent =
            "Please enter your password.";

        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "Checking...";

    loginMessage.textContent = "";

    try {

        const response = await fetch(
            API_URL + "/api/login",
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    password: password
                })
            }
        );

        const data = await response.json();

        if (response.ok && data.status === "success") {

            passwordInput.value = "";

            showAuthenticated();

            responseBox.textContent =
                JSON.stringify(
                    {
                        status: "ready",
                        message: "Authentication successful. Enter a number.",
                        Developer: "daruldark"
                    },
                    null,
                    2
                );

        } else {

            loginMessage.textContent =
                data.message || "Login failed.";

        }

    } catch (error) {

        loginMessage.textContent =
            "Could not connect to API.";

    } finally {

        loginButton.disabled = false;
        loginButton.textContent = "Login";

    }
}


// ============================================================
// LOGOUT
// ============================================================

async function logout() {

    try {

        await fetch(
            API_URL + "/api/logout",
            {
                method: "POST",
                credentials: "include"
            }
        );

    } catch (error) {

        console.error(error);

    }

    showLogin();

    responseBox.textContent =
        JSON.stringify(
            {
                status: "logged_out",
                message: "Please login to continue.",
                Developer: "daruldark"
            },
            null,
            2
        );
}


// ============================================================
// LOOKUP
// ============================================================

async function lookup() {

    const number = numberInput.value.trim();
    const database = databaseInput.value;

    if (!number) {

        responseBox.textContent =
            JSON.stringify(
                {
                    status: "rejected",
                    message: "Please enter a number.",
                    Developer: "daruldark"
                },
                null,
                2
            );

        return;
    }

    if (!/^\d{10,15}$/.test(number)) {

        responseBox.textContent =
            JSON.stringify(
                {
                    status: "rejected",
                    message: "Enter a valid 10-15 digit number.",
                    Developer: "daruldark"
                },
                null,
                2
            );

        return;
    }

    runButton.disabled = true;
    runButton.textContent = "Searching...";

    responseBox.textContent = "Searching database...";

    try {

        const url =
            API_URL +
            "/api/lookup?number=" +
            encodeURIComponent(number) +
            "&database=" +
            encodeURIComponent(database);

        const response = await fetch(
            url,
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data = await response.json();

        if (response.status === 401) {

            showLogin();

            responseBox.textContent =
                JSON.stringify(
                    data,
                    null,
                    2
                );

            return;
        }

        responseBox.textContent =
            JSON.stringify(
                data,
                null,
                2
            );

    } catch (error) {

        responseBox.textContent =
            JSON.stringify(
                {
                    status: "error",
                    message: "Could not connect to API.",
                    Developer: "daruldark"
                },
                null,
                2
            );

    } finally {

        runButton.disabled = false;
        runButton.textContent = "Run →";

    }
}


// ============================================================
// ENTER KEY
// ============================================================

if (passwordInput) {

    passwordInput.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {
                login();
            }

        }
    );
}


if (numberInput) {

    numberInput.addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {
                lookup();
            }

        }
    );
}


// ============================================================
// UI STATE
// ============================================================

function showLogin() {

    if (loginPanel) {
        loginPanel.style.display = "block";
    }

    if (lookupPanel) {
        lookupPanel.style.display = "none";
    }

    if (logoutButton) {
        logoutButton.style.display = "none";
    }

}


function showAuthenticated() {

    if (loginPanel) {
        loginPanel.style.display = "none";
    }

    if (lookupPanel) {
        lookupPanel.style.display = "block";
    }

    if (logoutButton) {
        logoutButton.style.display = "inline-block";
    }

}