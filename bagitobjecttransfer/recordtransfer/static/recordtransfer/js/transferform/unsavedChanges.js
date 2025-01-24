document.addEventListener("DOMContentLoaded", () => {
    const transferUuid = new URLSearchParams(window.location.search).get("transfer_uuid");
    
    // Skip click-away protection if on the first step of a fresh form
    if (currentFormStep <= 1 && !transferUuid) {
        return;
    }

    const beforeUnloadListener = (event) => {
        event.preventDefault();
        event.returnValue = "";
    };

    const elements = {
        modal: document.getElementById("unsaved-transferform-modal"),
        saveButton: document.getElementById("modal-save-button"),
        closeButton: document.getElementById("close-modal-button"),
        cancelButton: document.getElementById("unsaved-transferform-modal-cancel"),
        leaveButton: document.getElementById("unsaved-transferform-modal-leave"),
        formSaveButton: document.getElementById("form-save-button")
    };

    // The URL to navigate to when the user chooses to leave the form
    let targetUrl = "";

    const hideModal = () => elements.modal.classList.remove("visible");
    const showModal = () => elements.modal.classList.add("visible");

    // Add event listeners to only navigational links
    document.querySelectorAll("a:not(.non-nav-link)").forEach(link => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            targetUrl = event.currentTarget.href;
            showModal();
        });
    });

    elements.saveButton.addEventListener("click", (event) => {
        event.preventDefault();
        // Save and submit the form using the form's save button
        elements.formSaveButton.click();
        hideModal();
    });

    elements.closeButton.addEventListener("click", hideModal);
    elements.cancelButton.addEventListener("click", hideModal);

    elements.leaveButton.addEventListener("click", () => {
        window.removeEventListener("beforeunload", beforeUnloadListener);
        window.location.href = targetUrl;
    });

    // Elements that should not trigger the browser warning dialog
    const safeElements = [
        document.getElementById("form-next-button"),
        document.getElementById("form-previous-button"),
        document.getElementById("submit-form-btn"),
        elements.formSaveButton,
    ];

    safeElements.forEach(element => {
        if (element) {
            element.addEventListener("click", () => {
                window.removeEventListener("beforeunload", beforeUnloadListener);
            });
        }
    });

    window.addEventListener("beforeunload", beforeUnloadListener);
});