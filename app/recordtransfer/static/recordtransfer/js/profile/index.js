import { handleDeleteAfterRequest } from "./delete_ip_submission.js";
import { setupProfileForm } from "./profileForm.js";
import { initTabListeners, restoreTab } from "./tab.js";
import { setupToastNotifications } from "./toast.js";


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

    // Wrapper function that provides context to handleDeleteAfterRequest
    window.handleDeleteAfterRequest = (e) => {
        if (!context) {
            console.error("Context not available for handleDeleteAfterRequest");
            return;
        }
        return handleDeleteAfterRequest(e, context);
    };
}

document.addEventListener("DOMContentLoaded", initialize);