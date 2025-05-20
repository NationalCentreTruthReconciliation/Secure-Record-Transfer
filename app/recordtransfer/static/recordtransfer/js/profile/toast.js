/**
 * Utility to show toast notifications.
 */

const TOAST_CONTAINER_ID = "toast-container";

/**
 *
 * @param {string} type - The type of toast notification ('success', 'error', 'info', 'warning').
 * @param {string} message - The message to display in the toast notification.
 */
function showToast(type, message) {
    // Map type to alert class
    const typeClassMap = {
        success: "alert-success",
        error: "alert-error",
        info: "alert-info",
        warning: "alert-warning"
    };

    // Map type to icon
    const typeIconMap = {
        success: "<i class=\"fas fa-check-circle\"></i>",
        error: "<i class=\"fas fa-exclamation-circle\"></i>",
        warning: "<i class=\"fas fa-exclamation-triangle\"></i>",
        info: "<i class=\"fas fa-info-circle\"></i>"
    };

    const alertClass = typeClassMap[type] || "alert-info";
    const iconHtml = typeIconMap[type] || typeIconMap.info;

    // Find or create the toast container
    let toastContainer = document.getElementById(TOAST_CONTAINER_ID);
    if (!toastContainer) {
        toastContainer = document.createElement("div");
        toastContainer.className = "toast toast-top toast-center";
        toastContainer.id = TOAST_CONTAINER_ID;
        document.body.appendChild(toastContainer);
    }

    // Create the alert element
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert ${alertClass}`;

    // Add icon
    const iconSpan = document.createElement("span");
    iconSpan.innerHTML = iconHtml;
    iconSpan.className = "mr-2";
    alertDiv.appendChild(iconSpan);

    // Add message
    const messageSpan = document.createElement("span");
    messageSpan.textContent = message;
    alertDiv.appendChild(messageSpan);

    // Add to DOM
    toastContainer.appendChild(alertDiv);

    // Remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
        // Remove container if empty
        if (toastContainer.children.length === 0) {
            toastContainer.remove();
        }
    }, 5000);
}

// Convenience functions
/**
 * Shows a success toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
function showSuccessToast(message) {
    showToast("success", message);
}
/**
 * Shows an error toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
function showErrorToast(message) {
    showToast("error", message);
}
/**
 * Shows an info toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
function showInfoToast(message) {
    showToast("info", message);
}
/**
 * Shows a warning toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
function showWarningToast(message) {
    showToast("warning", message);
}

// HTMX Event Listeners for Toast Notifications
document.addEventListener("DOMContentLoaded", () => {
    if (window.htmx) {
        window.htmx.on("showSuccess", (event) => {
            showSuccessToast(event.detail.value);
        });

        window.htmx.on("showError", (event) => {
            showErrorToast(event.detail.value);
        });

        window.htmx.on("showInfo", (event) => {
            showInfoToast(event.detail.value);
        });

        window.htmx.on("showWarning", (event) => {
            showWarningToast(event.detail.value);
        });
    }
});