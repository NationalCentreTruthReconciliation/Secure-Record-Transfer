import {
    handleSubmissionGroupModalFormBeforeSwap,
    handleSubmissionGroupModalFormAfterSwap
} from "../utils/htmx.js";

const noDescription = "No description available";

/**
 * The entry point for setting up the submission group form.
 * This function initializes the form by setting up event listeners for the select field,
 * fetching group descriptions, and handling the modal swap events.
 * @param {object} context - The context object containing URLs and element IDs for the form.
 */
export async function setupSubmissionGroupForm(context) {
    console.log("Setting up submission group form with context:", context);
    const selectField = document.getElementById(context["id_submission_group_selection"]);
    const groupDescDisplay = document.getElementById(context["id_display_group_description"]);

    selectField.addEventListener("change", () =>
        updateGroupDescription(selectField, groupDescDisplay)
    );

    window.handleModalBeforeSwap = (e) => {
        return handleSubmissionGroupModalFormBeforeSwap(e, context);
    };
    window.handleModalAfterSwap = (e) => {
        return handleSubmissionGroupModalFormAfterSwap(e, context);
    };
    setupSubmissionGroupCreatedEventListener(selectField);

    // Set the initial content of the group description
    // This will be updated after the group descriptions have been fetched asynchronously
    groupDescDisplay.textContent = noDescription;

    // Fetch the group descriptions and set them on the options
    await fetchSubmissionGroups(context);

    // Select the default group at first
    selectGroup(context["default_group_uuid"], selectField);
    updateGroupDescription(selectField, groupDescDisplay);
}

/**
 * Updates the group description display based on the currently selected group in the select field.
 * If no group is selected or the selected group has no description, it displays a default message.
 * @param {HTMLSelectElement} selectField - The select field containing submission groups.
 * @param {HTMLElement} groupDescDisplay - The element where the group description will be
 * displayed.
 */
const updateGroupDescription = (selectField, groupDescDisplay) => {
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

/**
 * Fetches the submission groups from the server and populates the select field options. This
 * function should only be called once when the submission group form is initialized.
 * @param {object} context - The context object containing the URL to fetch group descriptions.
 */
const fetchSubmissionGroups = async (context) => {
    const response = await fetch(context["fetch_group_descriptions_url"], {
        method: "GET"
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const groups = await response.json();

    // Populate the select option data-attributes with the fetched group descriptions
    groups.forEach(function (group) {
        document.querySelector(`option[value='${group.uuid}']`)
            .setAttribute("data-description", group.description);
    });
};

/**
 * Selects a group in the select field by its UUID.
 * @param {string} groupUUID - The UUID of the group to select.
 * @param {HTMLSelectElement} selectField - The select field where the group should be selected.
 */
const selectGroup = (groupUUID, selectField) => {
    if (!groupUUID) {
        return;
    }
    selectField.value = groupUUID;
    selectField.dispatchEvent(new Event("change"));
};

/**
 * Handles the addition of a new group to the select field.
 * This function creates a new option element, sets its value and description,
 * appends it to the select field, and selects it.
 * @param {object} group - The group object containing name and uuid.
 * @param {HTMLSelectElement} selectField - The select field where the new group should be added.
 */
const handleNewGroupAdded = (group, selectField) => {
    const option = new Option(group.name, group.uuid);
    option.setAttribute("data-description", group.description);
    selectField.append(option);
    selectGroup(group.uuid, selectField);
};

/**
 * Sets up the event listener for the submissionGroupCreated event.
 * This event is triggered by a server response when a new submission group is created.
 * @param {HTMLSelectElement} selectField - The select field where the new group should be added.
 */
const setupSubmissionGroupCreatedEventListener = (selectField) => {
    if (!window.htmx) {
        return;
    }
    window.htmx.on("submissionGroupCreated", (event) => {
        handleNewGroupAdded(event.detail.group, selectField);
    });
};