/**
 * Sets up the functionality for dismissible alert messages
 * @returns {void}
 */
export function setupMessages() {
    const closeButtons = document.querySelectorAll("button.close[data-dismiss=alert]");
    closeButtons.forEach(button => {
        button.addEventListener("click", (event) => {
            event.target.closest(".alert-dismissible").style.display = "none";
        });
    });
}
