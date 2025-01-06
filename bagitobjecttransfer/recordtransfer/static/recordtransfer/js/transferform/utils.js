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
 * upload step of the transfer form.
 * @returns {?string} The value of the session token if found, null otherwise
 */
export const getSessionToken = () => {
    const sessionToken = document.querySelector("[id$=\"session_token\"]")?.getAttribute("value");
    return sessionToken || null;
};

/**
 * Sets the upload session token in the DOM.
 * Looks for an input element with an ID ending in "session_token", which should exist on the
 * upload step of the transfer form.
 * @param {string} token - The session token to set
 */
export const setSessionToken = (token) => {
    const sessionTokenElement = document.querySelector("[id$=\"session_token\"]");
    if (sessionTokenElement) {
        sessionTokenElement.setAttribute("value", token);
    }
};

/**
 * Retrieves file upload settings from context passed from view.
 * @returns {?object} The parsed JSON settings object if element exists, null otherwise.
 */
export const getSettings = () => {
    const settingsElement = document.getElementById("py_context_file_upload_settings");
    if (!settingsElement) {
        return null;
    }
    return JSON.parse(settingsElement.textContent);
};

export const fetchUploadedFiles = async () => {
    const sessionToken = getSessionToken();
    if (!sessionToken) {
        console.error("Cannot fetch uploaded files without a session token");
        return;
    }
    const response = await fetch(`/transfer/upload-session/${sessionToken}/files/`, {
        method: "GET",
    });
    if (!response.ok) {
        console.error("Failed to fetch uploaded files:", response.statusText);
        return null;
    }
    return response.json();
};

export const makeMockBlob = (size) => {
    const blob = new Blob([""], { type: "application/octet-stream" });
    Object.defineProperty(blob, "size", { value: size });
    return blob;
};

export const sendDeleteRequestForFile = async (filename) => {
    const sessionToken = getSessionToken();
    if (!sessionToken) {
        console.error("Cannot delete file without a session token");
        return;
    }
    const response = await fetch(`/transfer/upload-session/${sessionToken}/files/${filename}`, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
    });
    if (!response.ok) {
        console.error("Failed to delete file:", response.statusText);
    }

};