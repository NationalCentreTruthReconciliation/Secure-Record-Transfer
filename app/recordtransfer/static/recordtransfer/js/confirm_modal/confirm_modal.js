
/**
 * Sets up a modal that asks a user to confirm an action before executing it.
 * @param {HTMLElement} triggerElement - The element that will trigger the confirmation modal to
 * open when clicked.
 * @param {Function} confirmCallback - The callback function to execute when the user confirms the
 * action.
 */
export function setupConfirmModal(triggerElement, confirmCallback) {
    const elements = {
        modal: document.getElementById("confirm-modal"),
        closeButton: document.getElementById("close-modal-button"),
        confirmButton: document.getElementById("confirm-button"),
        cancelButton: document.getElementById("cancel-button"),
    };

    const hideModal = () => elements.modal.classList.remove("visible");
    const showModal = () => elements.modal.classList.add("visible");

    // Show modal when triggerModalElement is clicked on
    triggerElement.addEventListener("click", (event) => {
        event.preventDefault();
        showModal();
    });

    elements.confirmButton.addEventListener("click", (event) => {
        event.preventDefault();
        confirmCallback();
        hideModal();
    });

    elements.closeButton.addEventListener("click", hideModal);
    elements.cancelButton.addEventListener("click", hideModal);
}
