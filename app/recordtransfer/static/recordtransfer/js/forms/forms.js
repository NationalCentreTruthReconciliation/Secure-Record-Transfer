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

/**
 * Disable the "Create group" button if the group name is empty
 * @param {object} context - The context object containing form element IDs
 * @param {string} context.id_submission_group_name - The ID of the group name input element
 */
export const setupSubmissionGroupForm = (context) => {
    const groupName = document.getElementById(context["ID_SUBMISSION_GROUP_NAME"]);
    const saveButton = document.getElementById("id_create_group_button");

    const checkForChanges = () => {
        saveButton.disabled = !groupName.value;
    };

    groupName.addEventListener("input", checkForChanges);
    checkForChanges();
};

/**
 * Sets up the assign submission group form by enabling dynamic group description updates
 * and controlling the change button state based on selection changes.
 * @returns {void}
 */
export const setupAssignSubmissionGroupForm = () => {
    const selectElement = document.getElementById("group_select");
    const descriptionDisplay = document.getElementById("group_description_display");
    const changeGroupButton = document.getElementById("change_group_btn");
    const initialSelectedIndex = selectElement.selectedIndex;

    const updateGroupDescription = () => {
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const description = selectedOption.getAttribute("data-description");

        if (description) {
            descriptionDisplay.textContent = description;
        }
    };

    const updateChangeGroupButtonState = () => {
        const selectedIndex = selectElement.selectedIndex;
        changeGroupButton.disabled = selectedIndex === initialSelectedIndex;
    };

    if (!selectElement || !descriptionDisplay) {
        return;
    }

    selectElement.addEventListener("change", () => {
        updateGroupDescription();
        updateChangeGroupButtonState();
    });

    updateGroupDescription();
    updateChangeGroupButtonState();
};
