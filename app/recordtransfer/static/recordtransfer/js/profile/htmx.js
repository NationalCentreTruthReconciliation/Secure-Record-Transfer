import { addQueryParam, getCurrentTablePage } from "./utils.js";

/**
 * Handles the UI and table refresh after a delete request for an in-progress submission.
 *
 * Closes the delete confirmation modal and, if the request was successful,
 * refreshes the in-progress submissions table via HTMX AJAX.
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
export const handleDeleteIpSubmissionAfterRequest = (e, context) => {
    // Close the modal
    const modal = document.getElementById("base_modal");
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
