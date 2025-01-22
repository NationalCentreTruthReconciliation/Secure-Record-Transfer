
let groupDescriptions = {};

/**
 * Update the group description text to display based on the selected submission group.
 */
function updateGroupDescription() {
    const groupDescription = document.getElementById(ID_DISPLAY_GROUP_DESCRIPTION);
    const selectedGroupId = document.getElementById(ID_SUBMISSION_GROUP_SELECTION).value;
    let description = groupDescriptions[selectedGroupId];
    if (!description) {
        description = "No description available";
    }
    groupDescription.textContent = description;
}

/**
 * Asynchronously populates group descriptions by making an AJAX request to fetch user group
 * descriptions.
 *
 * @returns {Promise<void>} A promise that resolves when the group descriptions have been
 * successfully populated or rejects if the AJAX request fails.
 */
async function populateGroupDescriptions() {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: fetchUsersGroupDescriptionsUrl,
            success: function (groups) {
                groups.forEach(function (group) {
                    groupDescriptions[group.uuid] = group.description;
                });
                resolve();
            },
            error: function () {
                alert('Failed to populate group descriptions.');
                reject();
            }
        });
    });
}

/**
 * Handles the addition of a new group to the selection field.
 * @param {Object} group - The group object containing details of the new group.
 * The `group` object should have the following properties:
 * - `name` (String): The name of the group.
 * - `uuid` (String): The UUID of the group.
 * - `description` (String): The description of the group.
 */
function handleNewGroupAdded(group) {
    const selectField = document.getElementById(ID_SUBMISSION_GROUP_SELECTION);
    selectField.append(new Option(group.name, group.uuid));
    groupDescriptions[group.uuid] = group.description;
    selectField.value = group.uuid;
    selectField.dispatchEvent(new Event('change'));
}

function clearCreateGroupForm() {
    const groupName = document.getElementById(ID_SUBMISSION_GROUP_NAME);
    const groupDesc = document.getElementById(ID_SUBMISSION_GROUP_DESCRIPTION);
    groupName.value = "";
    groupDesc.value = "";
}

/**
 * Sets up the modal version of the submission group form.
 */
export async function setupSubmissionGroupModal() {
    const addNewGroupButton = document.getElementById("show-add-new-group-dialog");
    const contextElement = document.getElementById("py_context_submission_group");

    if (!addNewGroupButton || !context) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    const selectField = document.getElementById(context["id_submission_group_selection"]);

    const selectGroup = (groupUUID) => {
        selectField.value = groupUUID;
        selectField.dispatchEvent(new Event("change"));
        updateGroupDescription();
    };

    const handleNewGroupAdded = (group) => {
        selectField.append(new Option(group.name, group.uuid));
        selectGroup(group.uuid);
    };

    await populateGroupDescriptions();

    selectGroup(context?.default_group_id);

    updateGroupDescription();

    const createNewGroupForm = document.getElementById("submission-group-form");
    const createNewGroupModal = document.getElementById("create-new-submissiongroup-modal");
    const closeModalButton = document.getElementById("close-new-submissiongroup-modal");

    const hideCreateNewGroupModal = () => createNewGroupModal.classList.remove("visible");
    const showCreateNewGroupModal = () => createNewGroupModal.classList.add("visible");

    addNewGroupButton.addEventListener("click", function (event) {
        event.preventDefault();
        showCreateNewGroupModal();
    });

    closeModalButton.addEventListener("click", function (event) {
        event.preventDefault();
        hideCreateNewGroupModal();
    });

    createNewGroupForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const formData = new FormData(this);

        fetch(this.action, {
            method: this.method,
            body: formData,
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            }
        })
            .then(response => {
                if (!response.ok) {
                    return Promise.reject(response);
                }

                return response.json();
            })
            .then(data => {
                if (data.group) {
                    clearCreateGroupForm();
                    handleNewGroupAdded(data.group);
                    hideCreateNewGroupModal();
                }
            })
            .catch(response => {
                response.json().then(data => {
                    const message = data?.message ?? "Could not create submission group";
                    alert(message);
                });
            });
    });
}
