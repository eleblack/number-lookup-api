const API_URL =
    "https://number-lookup-api.onrender.com";


async function lookup() {

    const number =
        document
            .getElementById("number")
            .value
            .trim();


    const database =
        document
            .getElementById("database")
            .value;


    const responseBox =
        document.getElementById("response");


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


    responseBox.textContent =
        "Loading...";


    try {

        /*
         * The API requires an API key.
         *
         * Do NOT put the real API key in this
         * public JavaScript file.
         *
         * For a public website, authentication
         * should be handled by a protected backend.
         */

        const url =
            API_URL +
            "/api/lookup?number=" +
            encodeURIComponent(number) +
            "&database=" +
            encodeURIComponent(database);


        const response =
            await fetch(url);


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
                    message: "Could not connect to API.",
                    error: error.message,
                    Developer: "daruldark"
                },
                null,
                2
            );

    }

}