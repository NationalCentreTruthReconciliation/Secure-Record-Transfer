/**
 * Utility to show toast notifications.
 */

const TOAST_CONTAINER_ID = "toast-container";

/**
 * Displays a toast notification with the specified type and message.
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

    // Fade out and remove after 5 seconds
    setTimeout(() => {
        alertDiv.style.transition = "opacity 0.5s";
        alertDiv.style.opacity = "0";
        setTimeout(() => {
            alertDiv.remove();
            if (toastContainer.children.length === 0) {
                toastContainer.remove();
            }
        }, 500);
    }, 5000);
}

// Convenience functions
/**
 * Shows a success toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
export function showSuccessToast(message) {
    showToast("success", message);
}
/**
 * Shows an error toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
export function showErrorToast(message) {
    showToast("error", message);
}
/**
 * Shows an info toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
export function showInfoToast(message) {
    showToast("info", message);
}
/**
 * Shows a warning toast notification.
 * @param {string} message - The message to display in the toast notification.
 */
export function showWarningToast(message) {
    showToast("warning", message);
}

/**
 * Displays a stored toast notification from session storage if one exists.
 * This should be called on page load to show toasts from previous page actions.
 */
export function displayStoredToast() {
    const storedToast = sessionStorage.getItem("pendingToast");
    if (storedToast) {
        try {
            const toastData = JSON.parse(storedToast);

            if (toastData.showSuccess) {
                showSuccessToast(toastData.showSuccess.value);
            } else if (toastData.showError) {
                showErrorToast(toastData.showError.value);
            } else if (toastData.showInfo) {
                showInfoToast(toastData.showInfo.value);
            } else if (toastData.showWarning) {
                showWarningToast(toastData.showWarning.value);
            }

            // Clear the stored toast after displaying it
            sessionStorage.removeItem("pendingToast");
        } catch (error) {
            console.error("Failed to parse stored toast data:", error);
            sessionStorage.removeItem("pendingToast");
        }
    }
}

/**
 * Registers HTMX event listeners to show toast notifications for custom events.
 */
export const setupToastNotifications = () => {
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
};