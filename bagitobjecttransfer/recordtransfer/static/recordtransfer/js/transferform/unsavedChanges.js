document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const transferUuid = urlParams.get('transfer_uuid');
    
    // Skip click-away protection if on the first step of a fresh form
    if (currentFormStep <= 1 && !transferUuid) {
        return;
    }

    const beforeUnloadListener = (event) => {
        event.preventDefault();
        event.returnValue = '';
    };
    window.addEventListener('beforeunload', beforeUnloadListener);

    const modal = document.getElementById('unsaved-transferform-modal');
    const modalSaveButton = document.getElementById('modal-save-button');
    const closeButton = document.getElementById('close-modal-button');
    const cancelButton = document.getElementById('unsaved-transferform-modal-cancel');
    const leaveButton = document.getElementById('unsaved-transferform-modal-leave');
    let targetUrl = '';

    // Add event listeners to only navigational links
    document.querySelectorAll('a:not(.non-nav-link)').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            targetUrl = event.currentTarget.href;
            modal.classList.add('visible');
        });
    });

    modalSaveButton.addEventListener('click', (event) => {
        event.preventDefault();
        // Save and submit the form using the form's save button
        document.getElementById('form-save-button').click();
        modal.classList.remove('visible');
    });

    closeButton.addEventListener('click', () => {
        modal.classList.remove('visible');
    });

    cancelButton.addEventListener('click', () => {
        modal.classList.remove('visible');
    });

    leaveButton.addEventListener('click', () => {
        window.location.href = targetUrl;
    });

    // Elements that should not trigger the browser warning dialog
    const safeElements = [
        document.getElementById('form-next-or-submit-button'),
        document.getElementById('form-previous-button'),
        document.getElementById('form-save-button'),
    ];

    safeElements.forEach(element => {
        if (element) {
            element.addEventListener('click', () => {
                window.removeEventListener('beforeunload', beforeUnloadListener);
            });
        }
    });
});