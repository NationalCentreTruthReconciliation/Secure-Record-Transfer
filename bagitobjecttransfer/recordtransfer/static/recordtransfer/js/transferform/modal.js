document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('unsaved-transferform-modal');
    const saveButton = document.getElementById('modal-save-button');
    const closeButton = document.querySelector('.close-modal-button');
    const cancelButton = document.getElementById('unsaved-transferform-modal-cancel');
    
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
});