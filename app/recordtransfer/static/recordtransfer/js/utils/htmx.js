import { initializeSubmissionForm } from "../submission_form/index";
import { addQueryParam, getCurrentTablePage } from "./utils.js";

/**
 * Initialize custom events that are triggered by modal actions.
 *
 * This function creates modal-specific events that can be subscribed to. The purpose of these
 * events are to be more specific than general HTMX events.
 *
 * Following are the custom events that are set up:
 *
 * modal:beforeSwap - Triggered before swapping content in the modal container.
 * modal:afterSwap - Triggered after swapping content in the modal container.
 * modal:afterInProgressDelete - Triggered when an in-progress submission is deleted via a modal.
 * modal:afterGroupCreate - Triggered when a submission group is created via a modal.
 * modal:afterGroupChange - Triggered when a submission's group is changed via a modal.
 * modal:afterGroupDelete - Triggered when a submission group is deleted via a modal.
 */
export const initializeCustomModalEvents = () => {
    const modalContainer = document.getElementById("modal-content-container");

    if (null === modalContainer) {
        return;
    }

    // Custom "Before/after swap" events. See:
    // https://htmx.org/events/#htmx:beforeSwap
    // https://htmx.org/events/#htmx:afterSwap

    modalContainer.addEventListener(
        "htmx:beforeSwap", (event) => {
            document.dispatchEvent(
                new CustomEvent("modal:beforeSwap", { detail: event.detail })
            );
        }
    );

    modalContainer.addEventListener(
        "htmx:afterSwap", (event) => {
            document.dispatchEvent(
                new CustomEvent("modal:afterSwap", { detail: event.detail })
            );
        }
    );

    // Custom "After request" events using event delegation on the modal container.
    // These elements are dynamically loaded, so we listen on the container and check the target.
    // See: https://htmx.org/events/#htmx:afterRequest

    modalContainer.addEventListener(
        "htmx:afterRequest", (event) => {
            const triggeredBy = event.detail.requestConfig?.elt?.id;

            if (triggeredBy === "confirm_delete_ip_btn") {
                document.dispatchEvent(
                    new CustomEvent("modal:afterInProgressDelete", { detail: event.detail })
                );
            } else if (triggeredBy === "submission-group-form") {
                document.dispatchEvent(
                    new CustomEvent("modal:afterGroupCreate", { detail: event.detail })
                );
            } else if (triggeredBy === "assign-submission-group-form") {
                document.dispatchEvent(
                    new CustomEvent("modal:afterGroupChange", { detail: event.detail })
                );
            } else if (triggeredBy === "confirm_delete_submission_group_btn") {
                document.dispatchEvent(
                    new CustomEvent("modal:afterGroupDelete", { detail: event.detail })
                );
            }
        }
    );
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
export const refreshTable = (tableUrl, paginateQueryName, tableElementId) => {
    if (!document.getElementById(tableElementId)) {
        return;
    }

    const currentPage = getCurrentTablePage();
    const finalUrl = addQueryParam(tableUrl, paginateQueryName, currentPage);

    window.htmx.ajax("GET", finalUrl, {
        target: "#" + tableElementId,
        swap: "innerHTML"
    });
};

export const refreshSubmissionGroupTable = (context) => {
    refreshTable(
        context["SUBMISSION_GROUP_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_SUBMISSION_GROUP_TABLE"]
    );
};

export const refreshIPSubmissionTable = (context) => {
    refreshTable(
        context["IN_PROGRESS_SUBMISSION_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_IN_PROGRESS_SUBMISSION_TABLE"]
    );
};

export const refreshSubmissionTable = (context) => {
    refreshTable(
        context["SUBMISSION_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_SUBMISSION_TABLE"]
    );
};

export const refreshOpenSessionTable = (context) => {
    refreshTable(
        context["OPEN_SESSION_TABLE_URL"],
        context["PAGINATE_QUERY_NAME"],
        context["ID_OPEN_SESSION_TABLE"],
    );
};
