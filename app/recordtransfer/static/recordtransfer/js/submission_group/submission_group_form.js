const initializeSubmissionGroup = function () {
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
    const checkForChanges = function () {
        const nameChanged = groupName.value !== initialValues.submissionGroupName;
        const descriptionChanged =
            groupDescription.value !== initialValues.submissionGroupDescription;
        const hasChanged = nameChanged || descriptionChanged;
        saveButton.disabled = !hasChanged;
    };

    inputFields.forEach(function (input) {
        input.addEventListener("input", checkForChanges);
    });

    const deleteButton = document.getElementById("id_delete_group_button");
    deleteButton.addEventListener("click", function () {
        fetch(context["DELETE_URL"], {
            method: "DELETE",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            }
        }).then(function (response) {
            if (response.redirected) {
                window.location.href = response.url;
            }
        });
    });

    checkForChanges();
};

document.addEventListener("DOMContentLoaded", initializeSubmissionGroup);
