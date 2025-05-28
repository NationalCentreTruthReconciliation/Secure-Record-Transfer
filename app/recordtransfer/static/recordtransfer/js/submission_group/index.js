import {
    handleModalBeforeSwap
} from "../utils/htmx.js";
import { setupToastNotifications } from "../utils/toast.js";
import { showModal } from "../utils/utils.js";

document.addEventListener("DOMContentLoaded", function () {
    initialize();
});

/**
 * Initializes the submission group page functionality including form setup,
 * toast notifications, and modal handlers
 */
function initialize() {
    const context = getContext();
    if (!context) {return;}

    setupToastNotifications();
    setupSubmissionGroupForm(context);

    window.handleModalBeforeSwap = (e) => {
        return handleModalBeforeSwap(e, context);
    };

    window.handleModalAfterSwap = () => {
        showModal();
    };
}

/**
 * Gets the context object from the DOM element containing submission group data
 * @returns {object|null} The parsed context object or null if element not found
 */
function getContext() {
    const contextElement = document.getElementById("py_context_submission_group");
    if (!contextElement) {
        return null;
    }
    return JSON.parse(contextElement.textContent);
}

/**
 * Sets up the submission group form with validation and change detection
 * @param {object} context - The context object containing form field IDs
 * @param {string} context.ID_SUBMISSION_GROUP_NAME - The ID of the group name input field
 * @param {string} context.ID_SUBMISSION_GROUP_DESCRIPTION - The ID of the group description input
 * field
 */
function setupSubmissionGroupForm(context) {
    const groupName = document.getElementById(context["ID_SUBMISSION_GROUP_NAME"]);
    const groupDescription = document.getElementById(context["ID_SUBMISSION_GROUP_DESCRIPTION"]);
    const saveButton = document.getElementById("id_create_group_button");
    const initialGroupName = groupName.value;
    const initialGroupDescription = groupDescription.value;
    const inputFields = [groupName, groupDescription];
    const checkForChanges = () => {
        saveButton.disabled = !groupName.value ||
            (groupName.value === initialGroupName &&
             groupDescription.value === initialGroupDescription);
    };

    inputFields.forEach(input => {
        input.addEventListener("input", checkForChanges);
    });

    checkForChanges();
}