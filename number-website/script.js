const API_URL = "https://number-lookup-api.onrender.com";


// ============================================================
// NUMBER API LOOKUP
// ============================================================

async function lookup() {

    const numberInput = document.getElementById("number");
    const databaseInput = document.getElementById("database");
    const apiKeyInput = document.getElementById("apiKey");
    const responseBox = document.getElementById("response");

    const number = numberInput.value.trim();
    const database = databaseInput.value;
    const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";


    // --------------------------------------------------------
    // Validate number
    // --------------------------------------------------------

    if (!number) {

        responseBox.textContent = JSON.stringify(
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


    // --------------------------------------------------------
    // Validate number format
    // --------------------------------------------------------

    if (!/^\d{10,15}$/.test(number)) {

        responseBox.textContent = JSON.stringify(
            {
                status: "rejected",
                message: "Number must contain 10 to 15 digits.",
                Developer: "daruldark"
            },
            null,
            2
        );

        return;
    }


    // --------------------------------------------------------
    // Validate API key
    // --------------------------------------------------------

    if (!apiKey) {

        responseBox.textContent = JSON.stringify(
            {
                status: "rejected",
                message: "Please enter your API key.",
                Developer: "daruldark"
            },
            null,
            2
        );

        return;
    }


    // --------------------------------------------------------
    // Loading
    // --------------------------------------------------------

    responseBox.textContent = "Loading...";


    try {

        const url =
            API_URL +
            "/api/lookup?number=" +
            encodeURIComponent(number) +
            "&database=" +
            encodeURIComponent(database);


        // ----------------------------------------------------
        // API request
        // ----------------------------------------------------

        const response = await fetch(
            url,
            {
                method: "GET",

                headers: {
                    "X-API-Key": apiKey
                }
            }
        );


        // ----------------------------------------------------
        // Read JSON response
        // ----------------------------------------------------

        let data;

        try {

            data = await response.json();

        } catch (error) {

            data = {
                status: "error",
                message: "API returned an invalid response.",
                http_status: response.status,
                Developer: "daruldark"
            };

        }


        // ----------------------------------------------------
        // Display response
        // ----------------------------------------------------

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
                    details: error.message,
                    Developer: "daruldark"
                },
                null,
                2
            );

    }

}


// ============================================================
// ENTER KEY SUPPORT
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const numberInput =
            document.getElementById("number");

        const apiKeyInput =
            document.getElementById("apiKey");


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


        if (apiKeyInput) {

            apiKeyInput.addEventListener(
                "keydown",
                function (event) {

                    if (event.key === "Enter") {
                        lookup();
                    }

                }
            );

        }

    }
);