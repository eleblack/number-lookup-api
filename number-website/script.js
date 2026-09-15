const API_URL = "https://number-lookup-api.onrender.com";


// ============================================================
// LOOKUP
// ============================================================

async function lookup() {

    const numberInput = document.getElementById("number");
    const databaseInput = document.getElementById("database");
    const responseBox = document.getElementById("response");
    const button = document.getElementById("runButton");

    const number = numberInput.value.trim();
    const database = databaseInput.value;


    // --------------------------------------------------------
    // Validate empty number
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
    // Validate digits
    // --------------------------------------------------------

    if (!/^\d{10,15}$/.test(number)) {

        responseBox.textContent = JSON.stringify(
            {
                status: "rejected",
                message: "Enter a valid number containing 10 to 15 digits.",
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

    button.disabled = true;
    button.textContent = "Searching...";


    try {

        const url =
            API_URL +
            "/api/lookup?number=" +
            encodeURIComponent(number) +
            "&database=" +
            encodeURIComponent(database);


        const response = await fetch(url);


        let data;

        try {

            data = await response.json();

        } catch {

            data = {
                status: "error",
                message: "API returned an invalid response.",
                Developer: "daruldark"
            };

        }


        responseBox.textContent =
            JSON.stringify(data, null, 2);


    } catch (error) {

        responseBox.textContent =
            JSON.stringify(
                {
                    status: "error",
                    message: "Could not connect to NUMBER API.",
                    Developer: "daruldark"
                },
                null,
                2
            );

    } finally {

        button.disabled = false;
        button.textContent = "Run →";

    }
}


// ============================================================
// ENTER KEY
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const numberInput =
            document.getElementById("number");

        numberInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {
                    lookup();
                }

            }
        );

    }
);