import { refreshOpenSessionTable } from "../utils/htmx.js";
import { closeModal, showModal } from "../utils/utils.js";

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

    document.addEventListener("modal:afterSwap", () => {
        showModal();
    });

    document.addEventListener("modal:afterInProgressDelete", () => {
        closeModal();
        refreshOpenSessionTable(context);
    });
};
