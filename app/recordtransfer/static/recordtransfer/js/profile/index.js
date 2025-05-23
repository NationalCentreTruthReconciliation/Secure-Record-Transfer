import { setupProfileForm, setupSubmissionGroupForm } from "./forms.js";
import {
    handleDeleteIpSubmissionAfterRequest, handleModalBeforeSwap
} from "./htmx.js";
import { initTabListeners, restoreTab } from "./tab.js";
import { setupToastNotifications } from "./toast.js";
import { showModal } from "./utils.js";

/**
 * Main initialization function to set up all profile-related functionality
 */
function initialize() {
    let context = null;
    const contextElement = document.getElementById("py_context_user_profile");

    context = JSON.parse(contextElement.textContent);
    if (!context) {
        console.error("Context not available to set up profile page.");
        return;
    }

    setupProfileForm(context);
    initTabListeners();
    restoreTab();
    setupToastNotifications();

    // Wrapper function that provides context to handleDeleteIpSubmissionAfterRequest
    window.handleDeleteIpSubmissionAfterRequest = (e) => {
        return handleDeleteIpSubmissionAfterRequest(e, context);
    };

    // Wrapper function that provides context to handleModalBeforeSwap
    window.handleModalBeforeSwap = (e) => {
        return handleModalBeforeSwap(e, context);
    };

    window.handleModalAfterSwap = (e) => {
        // Sets up the submission group form if the modal content swap was triggered by the
        // new submission group button
        if (e.detail.requestConfig.elt.id === "id_new_submission_group_button") {
            setupSubmissionGroupForm(context);
        }
        // Always show the modal after a swap on the modal content container
        showModal();
    };
}

document.addEventListener("DOMContentLoaded", initialize);