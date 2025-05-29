/**
 * Gets the current page number of the table from the active tab
 * @returns {string|null} - The current page number or null if not found
 */
export function getCurrentTablePage() {
    // Find the active tab
    const activeTabInput = document.querySelector(
        ".tabs input[name=\"profile_tabs\"]:checked"
    );
    const activeTabContent = activeTabInput
        ? activeTabInput.closest(".tab").nextElementSibling
        : null;

    // Find the page-info-btn within the active tab content
    if (activeTabContent) {
        const pageInfoBtn = activeTabContent.querySelector(".page-info-btn");
        if (pageInfoBtn) {
            return pageInfoBtn.getAttribute("data-current-page");
        }
    }
    return null;
}

/**
 * Adds a query parameter to a URL.
 * @param {string} url - The base URL.
 * @param {string} paramName - The query parameter name.
 * @param {string|null} paramValue - The query parameter value.
 * @returns {string} - The URL with the query parameter appended if applicable.
 */
export function addQueryParam(url, paramName, paramValue) {
    if (paramName && paramValue) {
        const separator = url.includes("?") ? "&" : "?";
        return `${url}${separator}${paramName}=${encodeURIComponent(paramValue)}`;
    }
    return url;
}

/**
 * Closes the modal dialog.
 */
export function closeModal() {
    const modal = document.getElementById("base_modal");
    if (modal) {
        modal.close();
    }
}

/**
 * Opens the modal dialog.
 */
export function showModal() {
    const modal = document.getElementById("base_modal");
    if (modal) {
        modal.showModal();
    }
}

/**
 * Validates if a given string is a safe (from the same origin) and valid URL.
 * @param {string} url - The URL to validate.
 * @returns {boolean} True if the URL is valid, false otherwise.
 */
export function isValidUrl(url) {
    try {
        const parsedUrl = new URL(url, window.location.origin);
        return parsedUrl.origin === window.location.origin;
    } catch {
        return false;
    }
}
