document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const transferUuid = urlParams.get('transfer_uuid');
    
    // Skip click-away protection if on the first step of a fresh form
    if (currentFormStep <= 1 && !transferUuid) {
        return;
    }

    const modal = document.getElementById('unsaved-transferform-modal');
    const saveButton = document.getElementById('modal-save-button');
    const closeButton = document.querySelector('.close-modal-button');
    const cancelButton = document.getElementById('unsaved-transferform-modal-cancel');
    const leaveButton = document.getElementById('unsaved-transferform-modal-leave');
    let targetUrl = '';

    // Add event listeners to all links on page to unhide modal if clicked
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            targetUrl = event.currentTarget.href;
            modal.classList.add('visible');
        });
    });

    saveButton.addEventListener('click', (event) => {
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
});