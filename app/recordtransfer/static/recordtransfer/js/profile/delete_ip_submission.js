/**
 * Gets the current page number of the table from the active tab
 * @returns {string|null} - The current page number or null if not found
 */
function getCurrentTablePage() {
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
function addQueryParam(url, paramName, paramValue) {
    if (paramName && paramValue) {
        const separator = url.includes("?") ? "&" : "?";
        return `${url}${separator}${paramName}=${encodeURIComponent(paramValue)}`;
    }
    return url;
}

/**
 * Handles the UI and table refresh after a delete request for an in-progress submission.
 *
 * Closes the delete confirmation modal and, if the request was successful,
 * refreshes the in-progress submissions table via HTMX AJAX.
 *
 * @param {CustomEvent} e - The event object containing the request result in
 * `e.detail.successful`.
 * @param {object} context - Context object with URLs and element IDs for table refresh.
 * @param {string} context.IN_PROGRESS_SUBMISSION_TABLE_URL - The URL to refresh the in-progress
 * submissions table.
 * @param {string} context.PAGINATE_QUERY_NAME - The query parameter name for pagination
 * (e.g., "p").
 * @param {string} context.ID_IN_PROGRESS_SUBMISSION_TABLE - The DOM element ID of the in-progress
 * submissions table to update.
 */
export const handleDeleteAfterRequest = (e, context) => {
    // Close the modal
    const modal = document.getElementById("delete_in_progress_submission_modal");
    if (modal) {
        modal.close();
    }

    // If the request was successful, refresh the table
    if (e.detail.successful) {
        // Get base refresh URL
        const refreshUrl = context["IN_PROGRESS_SUBMISSION_TABLE_URL"];
        const paginateQueryName = context["PAGINATE_QUERY_NAME"];

        // Get the current page number
        const currentPage = getCurrentTablePage();

        const finalUrl = addQueryParam(refreshUrl, paginateQueryName, currentPage);

        window.htmx.ajax("GET",
            finalUrl,
            {
                target: "#" + context["ID_IN_PROGRESS_SUBMISSION_TABLE"],
                swap: "innerHTML"
            });
    }
};
