import {
    handleSubmissionGroupModalFormBeforeSwap,
    handleSubmissionGroupModalFormAfterSwap
} from "../utils/htmx.js";

/**
 * Sets up the modal version of the submission group form.
 * @param {object} context - The context object containing URLs and element IDs for the form.
 */
export async function setupSubmissionGroupForm(context) {

    window.handleModalBeforeSwap = (e) => {
        return handleSubmissionGroupModalFormBeforeSwap(e, context);
    };
    window.handleModalAfterSwap = (e) => {
        return handleSubmissionGroupModalFormAfterSwap(e, context);
    };

    const selectField = document.getElementById(context["id_submission_group_selection"]);
    const groupName = document.getElementById(context["ID_SUBMISSION_GROUP_NAME"]);
    const groupDesc = document.getElementById(context["ID_SUBMISSION_GROUP_DESCRIPTION"]);
    const groupDescDisplay = document.getElementById(context["id_display_group_description"]);
    const noDescription = "No description available";

    // Set the initial content of the group description
    // This will be updated after the group descriptions have been fetched asynchronously
    groupDescDisplay.textContent = noDescription;

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
                document.querySelector(`option[value='${group.uuid}']`)
                    .setAttribute("data-description", group.description);
            });

            updateGroupDescription();
        });

    const updateGroupDescription = () => {
        // Find the currently selected group
        const index = selectField.selectedIndex;

        // Set the group description to the data-description attribute from the selected option
        if (index > 0) {
            const selected = selectField.options[index];
            const description = selected.getAttribute("data-description").trim();

            if (!description) {
                groupDescDisplay.textContent = noDescription;
            }
            else {
                groupDescDisplay.textContent = description;
            }
        }
        else {
            groupDescDisplay.textContent = noDescription;
        }
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
    selectGroup(context?.default_group_uuid);

    selectField.addEventListener("change", updateGroupDescription);
}
