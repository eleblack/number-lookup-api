const API_URL = "https://number-lookup-api.onrender.com";

const loginPanel = document.getElementById("loginPanel");
const lookupPanel = document.getElementById("lookupPanel");

const passwordInput = document.getElementById("password");
const loginButton = document.getElementById("loginButton");
const logoutButton = document.getElementById("logoutButton");

const databaseSelect = document.getElementById("database");
const numberInput = document.getElementById("number");
const runButton = document.getElementById("runButton");

const responseBox = document.getElementById("response");


/* ============================================================
   DISPLAY HELPERS
   ============================================================ */

function showLogin() {
    if (loginPanel) {
        loginPanel.style.display = "block";
    }

    if (lookupPanel) {
        lookupPanel.style.display = "none";
    }
}


function showAuthenticated() {
    if (loginPanel) {
        loginPanel.style.display = "none";
    }

    if (lookupPanel) {
        lookupPanel.style.display = "block";
    }
}


function showResponse(data) {
    if (!responseBox) {
        return;
    }

    responseBox.textContent =
        JSON.stringify(data, null, 2);
}


function showMessage(message) {
    showResponse({
        message: message
    });
}


/* ============================================================
   SESSION CHECK
   ============================================================ */

async function checkSession() {

    try {

        const response = await fetch(
            `${API_URL}/api/session`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        const data = await response.json();

        if (data.authenticated) {
            showAuthenticated();
            await loadDatabases();
        } else {
            showLogin();
        }

    } catch (error) {

        console.error(error);

        showLogin();

        showMessage(
            "Unable to connect to the API."
        );
    }
}


/* ============================================================
   LOGIN
   ============================================================ */

async function login() {

    const password =
        passwordInput
            ? passwordInput.value
            : "";

    if (!password) {
        showMessage("Enter your password.");
        return;
    }

    try {

        if (loginButton) {
            loginButton.disabled = true;
        }

        const response = await fetch(
            `${API_URL}/api/login`,
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

        if (!response.ok) {

            showMessage({
                status: "error",
                message:
                    data.detail ||
                    "Login failed."
            });

            return;
        }

        if (passwordInput) {
            passwordInput.value = "";
        }

        showAuthenticated();

        await loadDatabases();

    } catch (error) {

        console.error(error);

        showMessage(
            "Unable to connect to the API."
        );

    } finally {

        if (loginButton) {
            loginButton.disabled = false;
        }
    }
}


/* ============================================================
   LOGOUT
   ============================================================ */

async function logout() {

    try {

        await fetch(
            `${API_URL}/api/logout`,
            {
                method: "POST",
                credentials: "include"
            }
        );

    } catch (error) {

        console.error(error);

    } finally {

        showLogin();
        showMessage("Logged out.");
    }
}


/* ============================================================
   LOAD DATABASES
   ============================================================ */

async function loadDatabases() {

    try {

        const response = await fetch(
            `${API_URL}/api/databases`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        if (response.status === 401) {
            showLogin();
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            showMessage(data);
            return;
        }

        if (!databaseSelect) {
            return;
        }

        databaseSelect.innerHTML = "";

        for (const database of data.databases) {

            const option =
                document.createElement("option");

            option.value = database.id;
            option.textContent = database.name;

            databaseSelect.appendChild(option);
        }

    } catch (error) {

        console.error(error);

        showMessage(
            "Unable to load databases."
        );
    }
}


/* ============================================================
   LOOKUP
   ============================================================ */

async function lookup() {

    const database =
        databaseSelect
            ? databaseSelect.value
            : "";

    const number =
        numberInput
            ? numberInput.value.trim()
            : "";

    if (!number) {
        showMessage("Enter a number.");
        return;
    }

    if (!/^\d+$/.test(number)) {
        showMessage(
            "Number must contain digits only."
        );
        return;
    }

    try {

        if (runButton) {
            runButton.disabled = true;
        }

        showMessage("Searching...");

        const params = new URLSearchParams();

        params.set("database", database);
        params.set("number", number);

        const response = await fetch(
            `${API_URL}/api/lookup?${params.toString()}`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        if (response.status === 401) {

            showLogin();

            showMessage(
                "Your session has expired. Please log in again."
            );

            return;
        }

        const data = await response.json();

        showResponse(data);

    } catch (error) {

        console.error(error);

        showMessage({
            status: "error",
            message:
                "Unable to connect to the API."
        });

    } finally {

        if (runButton) {
            runButton.disabled = false;
        }
    }
}


/* ============================================================
   EVENTS
   ============================================================ */

if (loginButton) {
    loginButton.addEventListener(
        "click",
        login
    );
}


if (logoutButton) {
    logoutButton.addEventListener(
        "click",
        logout
    );
}


if (runButton) {
    runButton.addEventListener(
        "click",
        lookup
    );
}


if (passwordInput) {
    passwordInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {
                login();
            }

        }
    );
}


if (numberInput) {
    numberInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {
                lookup();
            }

        }
    );
}


/* ============================================================
   START
   ============================================================ */

checkSession();