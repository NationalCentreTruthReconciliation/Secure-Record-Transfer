import { setupProfileForm } from "./profileForm.js";
import { initTabListeners, restoreTab } from "./tab.js";
import { setupToastNotifications } from "./toast.js";
import { handleDeleteIpSubmissionAfterRequest } from "./utils.js";


/**
 * Main initialization function to set up all profile-related functionality
 */
function initialize() {
    let context = null;
    const contextElement = document.getElementById("py_context_user_profile");

    if (contextElement) {
        context = JSON.parse(contextElement.textContent);
        setupProfileForm(context);
    }

    initTabListeners();
    restoreTab();
    setupToastNotifications();

    // Wrapper function that provides context to handleDeleteIpSubmissionAfterRequest
    window.handleDeleteIpSubmissionAfterRequest = (e) => {
        if (!context) {
            console.error("Context not available for handleDeleteIpSubmissionAfterRequest");
            return;
        }
        return handleDeleteIpSubmissionAfterRequest(e, context);
    };
}

document.addEventListener("DOMContentLoaded", initialize);