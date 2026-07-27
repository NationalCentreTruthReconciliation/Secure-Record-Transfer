/**
 * Set up a delegated click handler that closes modals when a close trigger is
 * clicked, without requiring inline scripts on each Cancel button.
 *
 * Any element marked with a `data-modal-close` attribute will close the nearest
 * enclosing `<dialog class="modal">` when clicked. This leverages the native
 * `HTMLDialogElement.close()` method provided by the DaisyUI modal component.
 *
 * Uses event delegation on `document` so that dynamically swapped-in modal
 * content (e.g. via HTMX) is handled without re-attaching listeners.
 */
export function setupModalClose(): void {
    document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }

        const trigger = target.closest("[data-modal-close]");
        if (!trigger) {
            return;
        }

        const modal = trigger.closest("dialog.modal");
        if (modal instanceof HTMLDialogElement) {
            modal.close();
        }
    });
}
