document.addEventListener("DOMContentLoaded", function () {
    const submissionGroupName = document.getElementById(ID_SUBMISSION_GROUP_NAME);
    const submissionGroupDescription = document.getElementById(ID_SUBMISSION_GROUP_DESCRIPTION);

    const inputFields = [submissionGroupName, submissionGroupDescription];
    const saveButton = document.getElementById("id_create_group_button");

    const initialValues = {
        submissionGroupName: submissionGroupName.value,
        submissionGroupDescription: submissionGroupDescription.value
    };

    function checkForChanges() {
        const submissionGroupNameChanged = submissionGroupName.value !== initialValues.submissionGroupName;
        const submissionGroupDescriptionChanged = submissionGroupDescription.value !== initialValues.submissionGroupDescription;

        const hasChanged = submissionGroupNameChanged || submissionGroupDescriptionChanged;
        saveButton.disabled = !hasChanged;
    }

    Array.from(inputFields).forEach(input => {
        input.addEventListener("input", checkForChanges);
    });

    checkForChanges();
});