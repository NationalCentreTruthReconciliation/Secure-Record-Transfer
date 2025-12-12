import {
    handleDeleteIpSubmissionAfterRequest,
    handleModalBeforeSwap,
    handleModalAfterSwap
} from "../utils/htmx.js";

/**
 * Main initialization function to set up session limit page.
 */
export const initializeSessionLimitPage = function() {
    let context = null;
    const contextElement = document.getElementById("py_context_session_limit_reached");

    if (!contextElement) {
        return;
    }

    context = JSON.parse(contextElement.textContent);
    if (!context) {
        console.error("Context not available to set up session limit page.");
        return;
    }

    // Wrapper functions to provide context to HTMX event handlers
    window.handleDeleteIpSubmissionAfterRequest = (e) => {
        return handleDeleteIpSubmissionAfterRequest(e, context);
    };

    window.handleModalBeforeSwap = (e) => {
        return handleModalBeforeSwap(e, context);
    };

    window.handleModalAfterSwap = (e) => {
        return handleModalAfterSwap(e, context);
    };
};
