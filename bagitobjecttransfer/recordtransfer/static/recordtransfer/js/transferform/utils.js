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