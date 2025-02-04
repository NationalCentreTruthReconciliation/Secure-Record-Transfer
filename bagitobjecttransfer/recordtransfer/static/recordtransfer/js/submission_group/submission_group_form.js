document.addEventListener("DOMContentLoaded", function () {
    const contextElement = document.getElementById("py_context_submission_group");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    const submissionGroupName = document.getElementById(context["id_submission_group_name"]);
    const submissionGroupDescription = document.getElementById(context["id_submission_group_description"]);

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
