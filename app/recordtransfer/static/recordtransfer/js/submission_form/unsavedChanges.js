
/**
 * Sets up a modal form that is displayed if a user tries to leave the page with unsaved changes.
 */
export function setupUnsavedChangesProtection() {
    const contextElement = document.querySelector("[id^='js_context_']");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);
    // Skip click-away protection if on the first step of a fresh form
    if (!context["FORM_STARTED"]) {
        return;
    }

    const beforeUnloadListener = (event) => {
        event.preventDefault();
        event.returnValue = "";
    };

    const elements = {
        get modal() { return document.getElementById("unsaved_changes_modal"); },
        get saveButton() { return document.getElementById("modal-save-link"); },
        get leaveButton() { return document.getElementById("unsaved-changes-leave-btn"); },
        get formSaveButton() { return document.getElementById("form-save-button"); }
    };

    // The URL to navigate to when the user chooses to leave the form
    let targetUrl = "";

    // Add event listeners to only navigational links
    document.querySelectorAll("a:not(.non-nav-link)").forEach(link => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            targetUrl = event.currentTarget.href;
            elements.modal.showModal();
        });
    });

    elements.saveButton.addEventListener("click", (event) => {
        event.preventDefault();
        // Save and submit the form using the form's save button
        elements.formSaveButton.click();
        elements.modal.close();
    });

    elements.leaveButton.addEventListener("click", () => {
        window.removeEventListener("beforeunload", beforeUnloadListener);
        window.location.href = targetUrl;
    });

    // Elements that should not trigger the browser warning dialog
    const safeElements = [
        document.getElementById("form-next-button"),
        document.getElementById("form-previous-button"),
        document.getElementById("form-review-button"),
        document.getElementById("submit-form-btn"),
        elements.formSaveButton,
        ...document.getElementsByClassName("step-link")
    ];

    safeElements.forEach(element => {
        if (element) {
            element.addEventListener("click", () => {
                window.removeEventListener("beforeunload", beforeUnloadListener);
            });
        }
    });

    window.addEventListener("beforeunload", beforeUnloadListener);
}
