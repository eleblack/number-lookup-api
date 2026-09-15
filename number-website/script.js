const API_URL = "https://number-lookup-api.onrender.com";


// =========================================================
// ELEMENTS
// =========================================================

const numberInput = document.getElementById("number");
const databaseInput = document.getElementById("database");
const responseBox = document.getElementById("response");


// =========================================================
// LOGIN UI
// =========================================================

function createLoginUI() {
    if (document.getElementById("loginPanel")) {
        return;
    }

    const apiCard = document.querySelector(".api-card");

    if (!apiCard) {
        return;
    }

    const panel = document.createElement("div");

    panel.id = "loginPanel";

    panel.style.marginBottom = "30px";
    panel.style.padding = "18px";
    panel.style.border = "1px solid #263449";
    panel.style.borderRadius = "10px";
    panel.style.background = "#0b111b";

    panel.innerHTML = `
        <div style="font-weight:700; margin-bottom:10px;">
            Authorized Access
        </div>

        <div style="font-size:13px; opacity:.8; margin-bottom:12px;">
            Enter your access password to use the NUMBER API.
        </div>

        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <input
                id="sitePassword"
                type="password"
                placeholder="Access password"
                autocomplete="current-password"
                style="
                    flex:1;
                    min-width:220px;
                    padding:12px;
                    border-radius:7px;
                    border:1px solid #263449;
                    background:#05090f;
                    color:white;
                "
            >

            <button
                id="loginButton"
                type="button"
                style="
                    padding:12px 20px;
                    border:0;
                    border-radius:7px;
                    cursor:pointer;
                "
            >
                Login
            </button>
        </div>

        <div
            id="loginMessage"
            style="
                margin-top:10px;
                font-size:13px;
            "
        ></div>
    `;

    apiCard.prepend(panel);

    document
        .getElementById("loginButton")
        .addEventListener("click", login);

    document
        .getElementById("sitePassword")
        .addEventListener("keydown", function(event) {
            if (event.key === "Enter") {
                login();
            }
        });
}


// =========================================================
// LOGIN
// =========================================================

async function login() {
    const passwordInput =
        document.getElementById("sitePassword");

    const loginMessage =
        document.getElementById("loginMessage");

    const loginButton =
        document.getElementById("loginButton");

    const password =
        passwordInput.value;

    if (!password) {
        loginMessage.textContent =
            "Please enter your password.";

        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";

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

        if (!response.ok) {
            loginMessage.textContent =
                data.message ||
                "Login failed.";

            return;
        }

        loginMessage.textContent =
            "Login successful.";

        passwordInput.value = "";

        updateLoginState(true);

        responseBox.textContent =
            JSON.stringify(
                {
                    status: "ready",
                    message:
                        "Authenticated. You can now run a lookup.",
                    Developer: "daruldark"
                },
                null,
                2
            );

    } catch (error) {
        loginMessage.textContent =
            "Could not connect to API.";

        console.error(error);

    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }
}


// =========================================================
// SESSION CHECK
// =========================================================

async function checkSession() {
    try {
        const response = await fetch(
            API_URL + "/api/session",
            {
                method: "GET",
                credentials: "include"
            }
        );

        if (response.ok) {
            updateLoginState(true);
            return true;
        }

    } catch (error) {
        console.error(
            "Session check failed:",
            error
        );
    }

    updateLoginState(false);

    return false;
}


// =========================================================
// LOGIN STATE UI
// =========================================================

function updateLoginState(authenticated) {
    const panel =
        document.getElementById("loginPanel");

    if (!panel) {
        return;
    }

    const existingLogout =
        document.getElementById("logoutButton");

    if (authenticated) {

        if (!existingLogout) {
            const logoutButton =
                document.createElement("button");

            logoutButton.id =
                "logoutButton";

            logoutButton.type =
                "button";

            logoutButton.textContent =
                "Logout";

            logoutButton.style.marginTop =
                "12px";

            logoutButton.style.padding =
                "8px 14px";

            logoutButton.style.borderRadius =
                "7px";

            logoutButton.style.border =
                "1px solid #263449";

            logoutButton.style.cursor =
                "pointer";

            logoutButton.addEventListener(
                "click",
                logout
            );

            panel.appendChild(
                logoutButton
            );
        }

    } else {

        if (existingLogout) {
            existingLogout.remove();
        }
    }
}


// =========================================================
// LOGOUT
// =========================================================

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

    updateLoginState(false);

    responseBox.textContent =
        JSON.stringify(
            {
                status: "logged_out",
                message:
                    "Please login to use the API.",
                Developer: "daruldark"
            },
            null,
            2
        );
}


// =========================================================
// LOOKUP
// =========================================================

async function lookup() {
    const number =
        numberInput.value.trim();

    const database =
        databaseInput.value;

    if (!number) {
        responseBox.textContent =
            JSON.stringify(
                {
                    status: "rejected",
                    message:
                        "Please enter a number.",
                    Developer: "daruldark"
                },
                null,
                2
            );

        return;
    }


    // Only allow digits in the browser.
    if (!/^\d+$/.test(number)) {
        responseBox.textContent =
            JSON.stringify(
                {
                    status: "rejected",
                    message:
                        "Number must contain digits only.",
                    Developer: "daruldark"
                },
                null,
                2
            );

        return;
    }


    responseBox.textContent =
        "Checking authorization...";


    try {

        const sessionResponse =
            await fetch(
                API_URL + "/api/session",
                {
                    method: "GET",
                    credentials: "include"
                }
            );


        if (!sessionResponse.ok) {

            responseBox.textContent =
                JSON.stringify(
                    {
                        status: "rejected",
                        message:
                            "Please login before using the API.",
                        Developer: "daruldark"
                    },
                    null,
                    2
                );

            updateLoginState(false);

            return;
        }


        responseBox.textContent =
            "Searching database...";


        const url =
            API_URL +
            "/api/lookup?number=" +
            encodeURIComponent(number) +
            "&database=" +
            encodeURIComponent(database);


        const response =
            await fetch(
                url,
                {
                    method: "GET",
                    credentials: "include"
                }
            );


        const data =
            await response.json();


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
                    message:
                        "Could not connect to API.",
                    Developer: "daruldark"
                },
                null,
                2
            );

        console.error(error);
    }
}


// =========================================================
// ENTER KEY
// =========================================================

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


// =========================================================
// START
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    async function() {

        createLoginUI();

        await checkSession();

    }
);