/**
 * Get a cookie's value by its name.
 * @param {string} name The name of the cookie to retrieve from the user
 * @returns {string} The cookie value. null if it does not exist
 */
export const getCookie = (name) => {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

/**
 * Retrieves the upload session token from the DOM.
 * Looks for an input element with an ID ending in "session_token", which should exist on the
 * upload step of the submission form.
 * @returns {?string} The value of the session token if found, null otherwise
 */
export const getSessionToken = () => {
    const sessionToken = document.querySelector("[id$=\"session_token\"]")?.getAttribute("value");
    return sessionToken || null;
};

/**
 * Fetches a new session token from the backend.
 * This function sends a POST request to the server to create a new upload session and retrieve
 * the session token.
 * @returns {Promise<string|null>} - A promise that resolves to the new session token, or null if
 * the request fails.
 */
export const fetchNewSessionToken = async () => {
    try {
        const response = await fetch("/upload-session/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },
        });

        if (response.ok) {
            const responseJson = await response.json();
            return responseJson.uploadSessionToken || null;
        } else {
            console.error("Failed to fetch new session token:", response.statusText);
            return null;
        }
    } catch (error) {
        console.error("Error fetching new session token:", error);
        return null;
    }
};

/**
 * Sets the upload session token in the DOM.
 * Looks for an input element with an ID ending in "session_token", which should exist on the
 * upload step of the submission form.
 * @param {string} token - The session token to set
 */
export const setSessionToken = (token) => {
    const sessionTokenElement = document.querySelector("[id$=\"session_token\"]");
    if (sessionTokenElement) {
        sessionTokenElement.setAttribute("value", token);
    }
};

/**
 * Fetches the list of uploaded files for the current upload session.
 * This function sends a GET request to the server to retrieve the list of uploaded files.
 * Uses exponential backoff to retry a total of 3 times if getting a 500 or more status.
 * @returns {Promise<object|null>} - A promise that resolves to the JSON response containing the
 * list of uploaded files, or null if the request fails or the session token is not available.
 */
export const fetchUploadedFiles = async () => {
    const sessionToken = getSessionToken();
    if (!sessionToken) {
        return null;
    }

    const maxRetries = 3;
    let attempt = 0;
    let response;

    while (attempt < maxRetries) {
        response = await fetch(`/upload-session/${sessionToken}/files/`, {
            method: "GET",
        });

        if (response.ok) {
            const responseJson = await response.json();
            if (!responseJson?.files) {
                console.error("Response is missing files");
                return null;
            }
            return responseJson.files;
        } else if (response.status >= 500) {
            attempt++;
            const delay = Math.pow(2, attempt) * 100; // Exponential backoff
            await new Promise(resolve => setTimeout(resolve, delay));
        } else {
            console.error("Failed to fetch uploaded files:", response.statusText);
            return null;
        }
    }

    console.error("Failed to fetch uploaded files after multiple attempts");
    return null;
};

/**
 * Creates a mock Blob object with a specified size without actually allocating memory for
 * the data content.
 * @param {number} size - The size of the Blob in bytes.
 * @returns {Blob} - A mock Blob object with the specified size.
 */
export const makeMockBlob = (size) => {
    const blob = new Blob([""], { type: "application/octet-stream" });
    Object.defineProperty(blob, "size", { value: size });
    return blob;
};

/**
 * Sends a DELETE request to remove an uploaded file from the server.
 * @param {string} filename - The name of the file to delete.
 * @returns {Promise<Response|null>} - A promise that resolves to the response of the request or
 * null if the session token was not found.
 */
export const sendDeleteRequestForFile = async (filename) => {
    const sessionToken = getSessionToken();
    if (!sessionToken) {
        console.error("Cannot delete file without a session token");
        return null;
    }
    const response = await fetch(`/upload-session/${sessionToken}/files/${filename}`, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
    });
    if (!response.ok) {
        console.error("Failed to delete file:", response.statusText);
    }
    return response;
};

/**
 * Updates the capacity display elements. Highlights the elements if the total size exceeds the
 * maximum allowed upload size.
 * @param {number} totalSizeBytes - The total size of the files in bytes.
 * @param {number} maxUploadSize - The maximum upload size in bytes.
 * @param {number} totalCount - The total number of files uploaded.
 * @param {number} maxCount - The maximum number of files allowed.
 */
export const updateCapacityDisplay = (totalSizeBytes, maxUploadSize, totalCount, maxCount) => {
    const totalSizeElement = document.getElementById("total-size");
    const remainingSizeElement = document.getElementById("remaining-size");
    const maxTotalUploadSizeBytes = maxUploadSize * 1000 * 1000;

    const totalCountElement = document.getElementById("files-count");
    const remainingCountElement = document.getElementById("remaining-files");
    const maxTotalUploadCount = maxCount;

    const updateElement = (element, value, isError, isInteger = false) => {
        if (element) {
            element.innerHTML = isInteger ? value.toString() : value.toFixed(2);
            element.classList.toggle("field-error", isError);
        }
    };

    const totalMB = totalSizeBytes / (1000 * 1000);
    const remainingMB = (maxTotalUploadSizeBytes - totalSizeBytes) / (1000 * 1000);

    const remainingFiles = maxTotalUploadCount - totalCount;

    updateElement(totalSizeElement, totalMB, totalSizeBytes > maxTotalUploadSizeBytes);
    updateElement(remainingSizeElement, Math.max(remainingMB, 0), remainingMB < 0);

    updateElement(totalCountElement, totalCount, totalCount > maxTotalUploadCount, true);
    updateElement(remainingCountElement, Math.max(remainingFiles, 0), remainingFiles < 0, true);

};