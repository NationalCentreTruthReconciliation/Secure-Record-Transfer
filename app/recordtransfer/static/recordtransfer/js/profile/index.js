import { setupProfileForm } from "../forms/forms.js";
import {
    handleDeleteIpSubmissionAfterRequest,
    handleDeleteSubmissionGroupAfterRequest,
    handleSubmissionGroupModalFormBeforeSwap,
    handleSubmissionGroupModalFormAfterSwap
} from "../utils/htmx.js";
import { setupToastNotifications, displayStoredToast } from "../utils/toast.js";
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
        return handleSubmissionGroupModalFormBeforeSwap(e, context);
    };

    window.handleModalAfterSwap = (e) => {
        return handleSubmissionGroupModalFormAfterSwap(e, context);
    };
};