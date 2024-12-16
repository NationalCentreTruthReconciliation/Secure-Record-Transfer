document.addEventListener("DOMContentLoaded", function () {
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

    function checkForChanges() {
        const firstNameChanged = firstName.value !== initialValues.firstName;
        const lastNameChanged = lastName.value !== initialValues.lastName;
        const notificationChanged = getsNotificationEmails.checked !== initialValues.getsNotificationEmails;

        const passwordFieldsPopulated = currentPassword.value !== "" &&
            newPassword.value !== "" &&
            confirmNewPassword.value !== "";

        const hasChanged = firstNameChanged || lastNameChanged || notificationChanged || passwordFieldsPopulated;
        saveButton.disabled = !hasChanged;
    }

    Array.from(inputFields).forEach(input => {
        input.addEventListener(input.type === "checkbox" ? "change" : "input", checkForChanges);
    });

    checkForChanges();

    // Save scroll position before page unload
    window.addEventListener('beforeunload', function () {
        localStorage.setItem('scrollPosition', window.scrollY);
    });

    // Restore scroll position after page load
    window.addEventListener('load', function () {
        const scrollPosition = localStorage.getItem('scrollPosition');
        if (scrollPosition !== null) {
            window.scrollTo(0, parseInt(scrollPosition, 10));
            localStorage.removeItem('scrollPosition');
        }
    });
});
