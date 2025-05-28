/**
 * Sets up the functionality for dismissible alert messages
 * @returns {void}
 */
export function setupMessages() {
    const closeButtons = document.querySelectorAll("button.close[data-dismiss=alert]");
    if (!closeButtons || closeButtons.length === 0) {
        return;
    }
    closeButtons.forEach(button => {
        button.addEventListener("click", (event) => {
            event.target.closest(".alert-dismissible").style.display = "none";
        });
    });
}
