import { setupSubmissionGroupForm, setupAssignSubmissionGroupForm } from "../forms/forms.js";
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

    if (e.detail.successful) {
        refreshIPSubmissionTable(context);
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
 * Handles the after-swap event for the modal.
 * This function is triggered after the modal content has been swapped in.
 * @param {Event} e - The HTMX after-swap event object containing request details
 * @param {object} context - The context object for the current operation
 * @returns {void}
 */
export const handleModalAfterSwap = (e, context) => {
    const triggeredBy = e.detail.requestConfig.elt.id;
    // Check if swap was triggered by the new submission group button
    if (triggeredBy === "id_new_submission_group_button") {
        setupSubmissionGroupForm(context);
    } else if (triggeredBy.startsWith("assign_submission_group_")) {
        setupAssignSubmissionGroupForm();
    }
    // Always show the modal after a swap on the modal content container
    showModal();
};

/**
 * Handles the modal swap event before content is replaced.
 * This function is triggered before the modal content is swapped and handles successful form
 * submissions by closing the modal and refreshing appropriate tables.
 * @param {CustomEvent} e - The event object containing the server response and request details.
 * @param {object} context - Context object with URLs and element IDs for table refresh.
 */
export const handleModalBeforeSwap = (e, context) => {
    // Only proceed if there's no server response (indicates successful form submission)
    if (!e.detail.serverResponse) {
        const triggeredBy = e.detail.requestConfig.elt.id;

        if (triggeredBy === "submission-group-form") {
            e.preventDefault(); // Stop the event from bubbling up
            closeModal();
            // Handler may be used on other pages where the submission group table is not present
            if (context["ID_SUBMISSION_GROUP_TABLE"] &&
                document.getElementById(context["ID_SUBMISSION_GROUP_TABLE"])) {
                refreshSubmissionGroupTable(context);
            }
        } else if (triggeredBy === "assign-submission-group-form") {
            e.preventDefault();
            closeModal();
            if (context["ID_SUBMISSION_TABLE"] &&
                document.getElementById(context["ID_SUBMISSION_TABLE"])) {
                refreshSubmissionTable(context);
            }
            if (context["ID_SUBMISSION_GROUP_TABLE"] &&
                document.getElementById(context["ID_SUBMISSION_GROUP_TABLE"])) {
                refreshSubmissionGroupTable(context);
            }
        }
    }
};

/**
 * Sets up global HTMX event listeners for application-wide behavior.
 * This should be called once in the main application entry point.
 */
export function setupBaseHtmxEventListeners() {
    document.addEventListener("htmx:afterSwap", (event) => {
        if (event.detail.target.id === "main-container") {
            initializeSubmissionForm();
        }
    });
}

/**
 * Generic function to refresh a table by making an HTMX AJAX request
 * @param {string} tableUrl - Base URL for fetching table data
 * @param {string} paginateQueryName - Query parameter name used for pagination
 * @param {string} tableElementId - DOM element ID of the table to update
 * @returns {void}
 */
const refreshTable = (tableUrl, paginateQueryName, tableElementId) => {
    const currentPage = getCurrentTablePage();
    const finalUrl = addQueryParam(tableUrl, paginateQueryName, currentPage);

    window.htmx.ajax("GET", finalUrl, {
        target: "#" + tableElementId,
        swap: "innerHTML"
    });
};

const refreshSubmissionGroupTable = (context) => {
    refreshTable(
        context["SUBMISSION_GROUP_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_SUBMISSION_GROUP_TABLE"]
    );
};

const refreshIPSubmissionTable = (context) => {
    refreshTable(
        context["IN_PROGRESS_SUBMISSION_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_IN_PROGRESS_SUBMISSION_TABLE"]
    );
};

const refreshSubmissionTable = (context) => {
    refreshTable(
        context["SUBMISSION_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_SUBMISSION_TABLE"]
    );
};