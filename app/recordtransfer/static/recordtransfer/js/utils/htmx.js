import { setupSubmissionGroupForm } from "../forms/forms.js";
import { initializeSubmissionForm } from "../submission_form/index";
import { addQueryParam, showModal, closeModal, getCurrentTablePage } from "./utils.js";

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
    closeModal();

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

export const handleDeleteSubmissionGroupAfterRequest = (e, context) => {
    closeModal();

    // If the request was successful, refresh the table
    if (e.detail.successful) {
        refreshSubmissionGroupTable(context);
    }
};

/**
 * Handles the after-swap event for submission group forms in HTMX contexts.
 * Sets up the submission group form when triggered by the new submission group button
 * and displays the modal after content swap.
 * @param {Event} e - The HTMX after-swap event object containing request details
 * @param {object} context - The context object for the current operation
 * @returns {void}
 */
export const handleSubmissionGroupModalFormAfterSwap = (e, context) => {
    // Sets up the submission group form if the modal content swap was triggered by the
    // new submission group button
    if (e.detail.requestConfig.elt.id === "id_new_submission_group_button") {
        setupSubmissionGroupForm(context);
    }
    // Always show the modal after a swap on the modal content container
    showModal();
};

/**
 * Handles the modal swap event before content is replaced.
 * Closes the modal if the server response is empty, which occurs when the submission group is
 * successfully created.
 * @param {CustomEvent} e - The event object containing the server response.
 * @param {object} context - Context object with URLs and element IDs for table refresh.
 * @param {string} context.SUBMISSION_GROUP_TABLE_URL - The URL to refresh the submission group
 * table.
 * @param {string} context.PAGINATE_QUERY_NAME - The query parameter name for pagination
 * (e.g., "p").
 * @param {string} context.ID_SUBMISSION_GROUP_TABLE - The DOM element ID of the submission group
 * table to update.
 */
export function handleSubmissionGroupModalFormBeforeSwap(e, context) {
    if (!e.detail.serverResponse && e.detail.requestConfig.elt.id === "submission-group-form") {
        e.preventDefault(); // Stop the event from bubbling up
        closeModal();
        // Handler may be used on other pages where the submission group table is not present
        if (context["ID_SUBMISSION_GROUP_TABLE"] &&
            document.getElementById(context["ID_SUBMISSION_GROUP_TABLE"])) {
            refreshSubmissionGroupTable(context);
        }
    }
}

/**
 * Refreshes the submission group table by making an HTMX AJAX request
 * @param {object} context - Configuration object containing URL and element identifiers
 * @param {string} context.SUBMISSION_GROUP_TABLE_URL - Base URL for fetching submission group
 * table data
 * @param {string} context.PAGINATE_QUERY_NAME - Query parameter name used for pagination
 * @param {string} context.ID_SUBMISSION_GROUP_TABLE - DOM element ID of the submission group table
 * to update
 * @returns {void}
 */
const refreshSubmissionGroupTable = (context) => {
    const refreshUrl = context["SUBMISSION_GROUP_TABLE_URL"];
    const paginateQueryName = context["PAGINATE_QUERY_NAME"];
    const currentPage = getCurrentTablePage();

    const finalUrl = addQueryParam(refreshUrl, paginateQueryName, currentPage);

    window.htmx.ajax("GET",
        finalUrl,
        {
            target: "#" + context["ID_SUBMISSION_GROUP_TABLE"],
            swap: "innerHTML"
        });
};

/**
 * Sets up global HTMX event listeners for application-wide behavior.
 * This should be called once in the main application entry point.
 */
export function setupBaseHtmxEventListeners() {
    document.body.addEventListener("htmx:beforeSwap", function(evt) {
        if (evt.detail.xhr.status === 422) {
            // allow 422 responses to swap as we are using this as a signal that
            // a form was submitted with bad data and want to rerender with the
            // errors
            // set isError to false to avoid error logging in console
            evt.detail.shouldSwap = true;
            evt.detail.isError = false;
        }
    });
    document.addEventListener("htmx:afterSwap", (event) => {
        if (event.detail.target.id === "main-container") {
            initializeSubmissionForm();
        }
    });
}
