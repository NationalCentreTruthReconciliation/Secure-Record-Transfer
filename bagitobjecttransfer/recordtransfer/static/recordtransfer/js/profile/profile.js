document.addEventListener("DOMContentLoaded", function () {
    const getsNotificationEmails = document.getElementById(ID_GETS_NOTIFICATION_EMAILS);
    const currentPassword = document.getElementById(ID_CURRENT_PASSWORD);
    const newPassword = document.getElementById(ID_NEW_PASSWORD);
    const confirmNewPassword = document.getElementById(ID_CONFIRM_NEW_PASSWORD);

    const inputFields = [getsNotificationEmails, currentPassword, newPassword, confirmNewPassword];

    const saveButton = document.getElementById("id_save_button");

    const initialValues = {
        getsNotificationEmails: getsNotificationEmails.checked,
        currentPassword: currentPassword.value,
        newPassword: newPassword.value,
        confirmNewPassword: confirmNewPassword.value
    };

    function checkForChanges() {
        const notificationChanged = getsNotificationEmails.checked !== initialValues.getsNotificationEmails;
        const passwordFieldsChanged = currentPassword.value !== initialValues.currentPassword &&
            newPassword.value !== initialValues.newPassword &&
            confirmNewPassword.value !== initialValues.confirmNewPassword;

        const hasChanged = notificationChanged || passwordFieldsChanged;
        saveButton.disabled = !hasChanged;
    }

    Array.from(inputFields).forEach(input => {
        input.addEventListener(input.type === "checkbox" ? "change" : "input", checkForChanges);
    });

    checkForChanges();
});