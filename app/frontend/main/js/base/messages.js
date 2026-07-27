/**
 * Sets up the functionality for dismissible alert messages using event delegation
 * @returns {void}
 */
export function setupMessages() {
    document.addEventListener("click", (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }

        const closeButton = event.target.closest("button.close[data-dismiss=alert]");
        if (!closeButton) {
            return;
        }

        closeButton.closest(".alert-dismissible")?.remove();
    });
}
