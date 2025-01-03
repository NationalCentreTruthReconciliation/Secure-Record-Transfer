/**
 * Get a cookie's value by its name.
 * @param {String} name The name of the cookie to retrieve from the user
 * @returns {String} The cookie value. null if it does not exist
 */
export const getCookie = (name) => {
    var cookieValue = null
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';')
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim()
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

/**
 * Retrieves the upload session token from the DOM.
 * Looks for an input element with an ID ending in "session_token", which should exist on the
 * upload step of the transfer form.
 * 
 * @returns {?string} The value of the session token if found, null otherwise
 */
export const getSessionToken = () => {
    const sessionToken = document.querySelector('[id$="session_token"]')?.getAttribute("value");
    return sessionToken || null;
};

/**
 * Sets the upload session token in the DOM.
 * Looks for an input element with an ID ending in "session_token", which should exist on the
 * upload step of the transfer form.
 * 
 * @param {string} token - The session token to set
 */
export const setSessionToken = (token) => {
    const sessionTokenElement = document.querySelector('[id$="session_token"]');
    if (sessionTokenElement) {
        sessionTokenElement.setAttribute("value", token);
    }
};

/**
 * Retrieves file upload settings from context passed from view.
 * @returns {?Object} The parsed JSON settings object if element exists, null otherwise.
 */
export const getSettings = () => {
    const settingsElement = document.getElementById("py_context_file_upload_settings");
    if (!settingsElement) {
        return null;
    }
    return JSON.parse(settingsElement.textContent);
}