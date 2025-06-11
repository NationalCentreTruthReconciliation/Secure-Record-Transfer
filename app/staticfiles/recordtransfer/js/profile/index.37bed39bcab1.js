import {
    handleDeleteIpSubmissionAfterRequest,
    handleDeleteSubmissionGroupAfterRequest,
    handleModalBeforeSwap
} from "../utils/htmx.js";
import { setupToastNotifications, displayStoredToast } from "../utils/toast.js";
import { showModal } from "../utils/utils.js";
import { setupProfileForm, setupSubmissionGroupForm } from "./forms.js";
import { initTabListeners, restoreTab } from "./tab.js";

/**
 * Main initialization function to set up all profile-related functionality
 */
export const initializeProfile = function() {
    let context = null;
    const contextElement = document.getElementById("py_context_user_profile");

    if (!contextElement) {
        return;
    }

    context = JSON.parse(contextElement.textContent);
    if (!context) {
        console.error("Context not available to set up profile page.");
        return;
    }

    setupProfileForm(context);
    initTabListeners();
    restoreTab();
    setupToastNotifications();
    displayStoredToast();

    // Wrapper functions to provide context to HTMX event handlers
    window.handleDeleteIpSubmissionAfterRequest = (e) => {
        return handleDeleteIpSubmissionAfterRequest(e, context);
    };

    window.handleDeleteSubmissionGroupAfterRequest = (e) => {
        return handleDeleteSubmissionGroupAfterRequest(e, context);
    };

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
};