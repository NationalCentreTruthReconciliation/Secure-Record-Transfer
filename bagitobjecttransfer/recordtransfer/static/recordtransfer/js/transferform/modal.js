document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('unsaved-transferform-modal');
    const saveButton = document.getElementById('modal-save-button');
    
    saveButton.addEventListener('click', (event) => {
        event.preventDefault();
        // Find and click the form's save button
        document.getElementById('form-save-button').click();
        // Close the modal
        modal.close();
    });
});