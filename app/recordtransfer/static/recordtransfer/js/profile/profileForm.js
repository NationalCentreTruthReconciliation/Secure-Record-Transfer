/**
 * Sets up the profile form by tracking changes to input fields and enabling the save button when
 * changes are detected.
 * @param {object} context - An object containing DOM element IDs for the profile form fields.
 * @param {string} context.ID_FIRST_NAME - The ID of the first name input field.
 * @param {string} context.ID_LAST_NAME - The ID of the last name input field.
 * @param {string} context.ID_GETS_NOTIFICATION_EMAILS - The ID of the notification emails
 * checkbox.
 * @param {string} context.ID_CURRENT_PASSWORD - The ID of the current password input field.
 * @param {string} context.ID_NEW_PASSWORD - The ID of the new password input field.
 * @param {string} context.ID_CONFIRM_NEW_PASSWORD - The ID of the confirm new password input
 * field.
 */
export const setupProfileForm = (context) => {
    const firstName = document.getElementById(context["ID_FIRST_NAME"]);
    const lastName = document.getElementById(context["ID_LAST_NAME"]);
    const getsNotificationEmails = document.getElementById(
        context["ID_GETS_NOTIFICATION_EMAILS"]
    );
    const currentPassword = document.getElementById(context["ID_CURRENT_PASSWORD"]);
    const newPassword = document.getElementById(context["ID_NEW_PASSWORD"]);
    const confirmNewPassword = document.getElementById(
        context["ID_CONFIRM_NEW_PASSWORD"]
    );

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
};
