const API_URL =
    "https://number-lookup-api.onrender.com";


// ============================================================
// LOOKUP
// ============================================================

async function lookup() {

    const numberInput =
        document.getElementById("number");

    const databaseInput =
        document.getElementById("database");

    const responseBox =
        document.getElementById("response");

    const button =
        document.getElementById("runButton");


    const number =
        numberInput.value.trim();

    const database =
        databaseInput.value;


    // ========================================================
    // VALIDATION
    // ========================================================

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
                    message:
                        "Number must contain 10 to 15 digits.",
                    Developer: "daruldark"
                },
                null,
                2
            );

        return;
    }


    // ========================================================
    // LOADING
    // ========================================================

    button.disabled = true;

    button.textContent =
        "Loading...";


    responseBox.textContent =
        "Searching database...";


    // ========================================================
    // API URL
    // ========================================================

    const url =
        API_URL +
        "/api/lookup?number=" +
        encodeURIComponent(number) +
        "&database=" +
        encodeURIComponent(database);


    // ========================================================
    // REQUEST
    // ========================================================

    try {

        const response =
            await fetch(url);


        let data;


        try {

            data =
                await response.json();

        } catch {

            data = {
                status: "error",
                message:
                    "API returned an invalid response.",
                Developer: "daruldark"
            };

        }


        // ====================================================
        // DISPLAY
        // ====================================================

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
                    error:
                        error.message,
                    Developer:
                        "daruldark"
                },
                null,
                2
            );

    }


    // ========================================================
    // RESET BUTTON
    // ========================================================

    button.disabled = false;

    button.textContent =
        "Run →";
}



// ============================================================
// ENTER KEY
// ============================================================

document
    .getElementById("number")
    .addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                lookup();

            }

        }
    );