/**
 * Get a cookie's value by its name.
 * @param {String} name The name of the cookie to retrieve from the user
 * @returns {String} The cookie value. null if it does not exist
 */
export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Appends an error message to the page in the dropzone-errors element.
 * @param {String} errorMessage The error message to show
 */
export function addDropzoneError(errorMessage) {
    const errorZone = document.getElementById('dropzone-errors');
    const newError = document.createElement('div');
    newError.className = 'field-error';
    newError.innerHTML = errorMessage;
    errorZone.appendChild(newError);
}

/**
 * Removes all errors shown in the dropzone-errors element.
 */
export function clearDropzoneErrors() {
    const errorZone = document.getElementById('dropzone-errors');
    while (errorZone.lastElementChild) {
        errorZone.removeChild(errorZone.lastElementChild);
    }
}