import {
    handleDeleteIpSubmissionAfterRequest, handleModalBeforeSwap
} from "./htmx.js";
import { setupProfileForm } from "./profileForm.js";
import { initTabListeners, restoreTab } from "./tab.js";
import { setupToastNotifications } from "./toast.js";


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
}

document.addEventListener("DOMContentLoaded", initialize);