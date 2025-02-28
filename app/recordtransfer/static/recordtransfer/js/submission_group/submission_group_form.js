document.addEventListener("DOMContentLoaded", function () {
    const contextElement = document.getElementById("py_context_submission_group");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    const groupName = document.getElementById(context["id_submission_group_name"]);
    const groupDescription = document.getElementById(
        context["id_submission_group_description"]
    );

    const inputFields = [groupName, groupDescription];
    const saveButton = document.getElementById("id_create_group_button");

    const initialValues = {
        submissionGroupName: groupName.value,
        submissionGroupDescription: groupDescription.value
    };

    /**
     * Checks if either the submission group name or description has changed. Enables the save
     * button if a change is detected, disables it otherwise.
     */
    function checkForChanges() {
        const nameChanged = groupName.value !== initialValues.submissionGroupName;
        const descriptionChanged =
            groupDescription.value !== initialValues.submissionGroupDescription;
        const hasChanged = nameChanged || descriptionChanged;
        saveButton.disabled = !hasChanged;
    }

    Array.from(inputFields).forEach(input => {
        input.addEventListener("input", checkForChanges);
    });

    checkForChanges();
});
