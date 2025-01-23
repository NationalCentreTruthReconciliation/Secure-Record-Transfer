/**
 * Sets up the modal version of the submission group form.
 */
export async function setupSubmissionGroupForm() {
    const addNewGroupButton = document.getElementById("show-add-new-group-dialog");
    const contextElement = document.getElementById("py_context_submission_group");

    if (!addNewGroupButton || !context) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    const selectField = document.getElementById(context["id_submission_group_selection"]);
    const groupName = document.getElementById(context["id_submission_group_name"]);
    const groupDesc = document.getElementById(context["id_submission_group_description"]);

    // Set the initial content of the group description
    // This will be updated after the group descriptions have been fetched asynchronously
    groupDesc.textContent = "No description available";

    // Fetch initial group descriptions when creating the form
    fetch(context["fetch_group_descriptions_url"], {
        method: "GET"
    })
        .then(response => {
            if (!response.ok) {
                return Promise.reject(response);
            }

            return response.json();
        })
        .then(groups => {
            // Apply the group description to the data-description attribute of each option
            groups.forEach(function (group) {
                console.log(`${group.uuid}: ${group.description}`);
            });

            updateGroupDescription();
        });

    const updateGroupDescription = () => {
        // Find the currently selected group

        // Set the group description to the data-description attribute from the selected option
    };

    const selectGroup = (groupUUID) => {
        if (!groupUUID) {
            return;
        }

        // Select the option
        selectField.value = groupUUID;
        selectField.dispatchEvent(new Event("change"));

        // And update the shown description
        updateGroupDescription();
    };

    const handleNewGroupAdded = (group) => {
        // Add a new option
        const option = new Option(group.name, group.uuid);
        option.setAttribute("data-description", group.description);
        selectField.append(option);

        // And select it
        selectGroup(group.uuid);
    };

    // Select the default group at first
    selectGroup(context?.default_group_id);

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
                    groupName.value = "";
                    groupDesc.value = "";
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
