import { setupProfileForm } from "../forms/forms.js";
import {
    handleDeleteIpSubmissionAfterRequest,
    handleDeleteSubmissionGroupAfterRequest,
    handleSubmissionGroupModalFormBeforeSwap,
    handleAssignSubmissionGroupModalBeforeSwap,
    handleModalAfterSwap
} from "../utils/htmx.js";
import { setupUserContactInfoForm } from "./contactInfo.js";
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
    setupUserContactInfoForm(context);
    initTabListeners();
    restoreTab();

    // Wrapper functions to provide context to HTMX event handlers
    window.handleDeleteIpSubmissionAfterRequest = (e) => {
        return handleDeleteIpSubmissionAfterRequest(e, context);
    };

    window.handleDeleteSubmissionGroupAfterRequest = (e) => {
        return handleDeleteSubmissionGroupAfterRequest(e, context);
    };

    window.handleModalBeforeSwap = (e) => {
        handleSubmissionGroupModalFormBeforeSwap(e, context);
        handleAssignSubmissionGroupModalBeforeSwap(e, context);
    };

    window.handleModalAfterSwap = (e) => {
        return handleModalAfterSwap(e, context);
    };

    window.setupProfileForm = () => {
        return setupProfileForm(context);
    };

    window.setupUserContactInfoForm = () => {
        return setupUserContactInfoForm(context);
    };
};