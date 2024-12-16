document.addEventListener("DOMContentLoaded", () => {
    const firstName = document.getElementById(ID_FIRST_NAME);
    const lastName = document.getElementById(ID_LAST_NAME);
    const getsNotificationEmails = document.getElementById(ID_GETS_NOTIFICATION_EMAILS);
    const currentPassword = document.getElementById(ID_CURRENT_PASSWORD);
    const newPassword = document.getElementById(ID_NEW_PASSWORD);
    const confirmNewPassword = document.getElementById(ID_CONFIRM_NEW_PASSWORD);

    const inputFields = [
        firstName,
        lastName,
        getsNotificationEmails,
        currentPassword,
        newPassword,
        confirmNewPassword
    ];

    const saveButton = document.getElementById("id_save_button");

    const initialValues = {
        firstName: firstName.value,
        lastName: lastName.value,
        getsNotificationEmails: getsNotificationEmails.checked,
    };

    const checkForChanges = () => {
        const hasChanged = firstName.value !== initialValues.firstName ||
            lastName.value !== initialValues.lastName ||
            getsNotificationEmails.checked !== initialValues.getsNotificationEmails ||
            (currentPassword.value && newPassword.value && confirmNewPassword.value);

        saveButton.disabled = !hasChanged;
    };

    inputFields.forEach(input => {
        input.addEventListener(input.type === "checkbox" ? "change" : "input", checkForChanges);
    });

    checkForChanges();

    // Save scroll position before page unload
    window.addEventListener('beforeunload', () => {
        localStorage.setItem('scrollPosition', window.scrollY);
    });

    // Restore scroll position after page load
    window.addEventListener('load', () => {
        const scrollPosition = localStorage.getItem('scrollPosition');
        if (scrollPosition) {
            window.scrollTo(0, parseInt(scrollPosition, 10));
            localStorage.removeItem('scrollPosition');
        }
    });
});
