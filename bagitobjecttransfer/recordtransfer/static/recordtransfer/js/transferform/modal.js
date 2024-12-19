document.addEventListener('DOMContentLoaded', () => {
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
            modal.classList.remove('hidden');
        });
    });

    saveButton.addEventListener('click', (event) => {
        event.preventDefault();
        // Save and submit the form using the form's save button
        document.getElementById('form-save-button').click();
        modal.close();
    });

    closeButton.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    cancelButton.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    leaveButton.addEventListener('click', () => {
        window.location.href = targetUrl;
    });
});