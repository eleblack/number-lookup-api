async function lookup() {

    const number = document.getElementById("number").value.trim();

    const responseBox = document.getElementById("response");

    if (!number) {
        responseBox.textContent = "Please enter a number.";
        return;
    }

    responseBox.textContent = "Loading...";

    try {

        const url =
            "https://number-lookup-api.onrender.com/?number=" +
            encodeURIComponent(number);

        const response = await fetch(url);

        const data = await response.json();

        responseBox.textContent =
            JSON.stringify(data, null, 2);

    } catch (error) {

        responseBox.textContent =
            JSON.stringify({
                status: "error",
                message: "Could not connect to API",
                error: error.message
            }, null, 2);
    }
}