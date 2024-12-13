/**
 * Functions and configuration for Django forms.
 *
 * Credit to this article for adding/removing forms from formsets:
 * https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
 */

let groupDescriptions = {};

/**
 * Function to setup on click handlers for select boxes to toggle text fields when selecting "Other"
 *
 * @param otherField : Array of selectors to return some objects.
 * @param choiceFieldFn : callable that converts the found text field id to the corresponding select box id
 *                        ie. id_rightsstatement-other_rights_statement_type => id_rightsstatement-rights_statement_type
 */
function setupSelectOtherToggle(otherField, choiceFieldFn) {
    if (otherField.some((selector) => $(selector).length)) {
        $.each(otherField, function (_, v) {
            // Use each as a single value in the otherField array could result in multiple objects, ie. class selector
            $(v).each(function () {
                let currentId = "#" + $(this).attr("id");
                let choiceField = choiceFieldFn(currentId);
                let value = $(choiceField + " option:selected").text().toLowerCase().trim()
                let state = value === 'other' ? 'on' : 'off'
                toggleFlexItems([currentId], state)
                // Remove any current event handlers
                $(choiceField).off('change');
                // Add the new event handlers
                $(choiceField).change(function () { onSelectChange.call(this, currentId) });
            });
        });
    }
}

/**
 * Function to toggle the visibility of the "other" text field based on the select box value.
 *
 * @param currentId : id of the "other" text field
 */
function onSelectChange(currentId) {
    let state = $("option:selected", this).text().toLowerCase().trim() === 'other' ? 'on' : 'off'
    toggleFlexItems([currentId], state)
}

/**
 * Alter the id of the "other" field to refer back to the select box.
 *
 * @param id : the id of the other text field.
 */
function removeOther(id) {
    let newId = id.replace('other_', '');
    if (!/^#/.test(newId)) {
        newId = "#" + newId;
    }
    return newId;
}

/**
 * Show or hide div.flex-items related to form fields.
 * @param {Array} selectors Form field selectors, the closest div.flex-items will be shown/hidden
 * @param {String} state Shows divs if 'on', hides divs if 'off', does nothing otherwise
 */
function toggleFlexItems(selectors, state) {
    if (state === 'on') {
        selectors.forEach(function (sel) {
            $(sel).closest('div.flex-item').show()
        })
    }
    else if (state === 'off') {
        selectors.forEach(function (sel) {
            $(sel).closest('div.flex-item').hide()
        })
    }
}

/**
 * Update the group description text to display based on the selected submission group.
 */
const updateGroupDescription = () => {
    const groupDescription = document.getElementById(ID_DISPLAY_GROUP_DESCRIPTION);
    const selectedGroupId = document.getElementById(ID_SUBMISSION_GROUP_SELECTION).value;
    let description = groupDescriptions[selectedGroupId];
    if (!description) {
        description = "No description available";
    }
    groupDescription.textContent = description;
}

/**
 * Asynchronously populates group descriptions by making an AJAX request to fetch user group descriptions.
 *
 * @returns {Promise<void>} A promise that resolves when the group descriptions have been successfully populated,
 * or rejects if the AJAX request fails.
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

function selectDefaultGroup(groupId) {
    if (groupId) {
        const selectField = $('#' + ID_SUBMISSION_GROUP_SELECTION);
        selectField.val(groupId).change();
    }
}

async function initializeGroupTransferForm() {
    await populateGroupDescriptions();
    selectDefaultGroup(DEFAULT_GROUP_ID);
    updateGroupDescription();
}

/**
 * Prevents the submission group form from submitting and instead sends an AJAX request to create a
 * new group. If the group is successfully created, the new group is added to the selection field,
 * and the description updated.
 */
function initializeModalMode() {
    $('#submission-group-form').off('submit').on('submit', function (event) {
        event.preventDefault();

        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: $(this).serialize(),
            success: async function (response) {
                clearCreateGroupForm();
                try {
                    handleNewGroupAdded(response.group);
                    $('#add-new-group-dialog').dialog("close");
                }
                catch (error) {
                    alert("Failed to update group options.");
                }
            },
            error: function (response) {
                alert(response.responseJSON.message);
            }
        });
    });
}

/**
 * Handles the addition of a new group to the selection field.
 *
 * @param {Object} group - The group object containing details of the new group.
 * The `group` object should have the following properties:
 * - `name` (String): The name of the group.
 * - `uuid` (String): The UUID of the group.
 * - `description` (String): The description of the group.
 */
function handleNewGroupAdded(group) {
    const selectField = $('#' + ID_SUBMISSION_GROUP_SELECTION);
    selectField.append(new Option(group.name, group.uuid));
    groupDescriptions[group.uuid] = group.description;
    selectField.val(group.uuid).change();
}

function clearCreateGroupForm() {
    const submissionGroupName = document.getElementById(ID_SUBMISSION_GROUP_NAME);
    const submissionGroupDescription = document.getElementById(ID_SUBMISSION_GROUP_DESCRIPTION);
    submissionGroupName.value = '';
    submissionGroupDescription.value = '';
}

document.addEventListener("DOMContentLoaded", function () {
    /***************************************************************************
     * Formset Setup
     **************************************************************************/
    const contextElement = document.getElementById("py_context_formset");

    // Set up adding and removing formset forms
    if (contextElement) {
        const contextContent = JSON.parse(contextElement.textContent);

        const prefix = contextContent.formset_prefix;
        const formRowRegex = new RegExp(`${prefix}-\\d+-`, 'g');

        const maxFormsInput = document.getElementById(`id_${prefix}-MAX_NUM_FORMS`);
        const maxForms = parseInt(maxFormsInput.getAttribute("value"));
        const totalFormsInput = document.getElementById(`id_${prefix}-TOTAL_FORMS`);

        let formsetForms = document.querySelectorAll('.form-row');
        let numForms = formsetForms.length;

        function refreshFormset() {
            formsetForms = document.querySelectorAll('.form-row');
            numForms = formsetForms.length;
            totalFormsInput.setAttribute('value', numForms);
        }

        const removeFormButton = document.querySelector(".remove-form-row");
        const addFormButton = document.querySelector(".add-form-row");

        function refreshButtonState() {
            removeFormButton.disabled = numForms <= 1;
            addFormButton.disabled = numForms >= maxForms;
        }

        refreshButtonState();

        // Remove the last form on click
        removeFormButton.addEventListener('click', function (event) {
            event.preventDefault();
            refreshFormset();

            if (numForms > 1) {
                const lastForm = formsetForms[formsetForms.length - 1];
                lastForm.remove();
            }

            refreshFormset();
            refreshButtonState();
        });

        // Add imminent-removal class to the last form when about to click the button
        removeFormButton.addEventListener('mouseenter', function (event) {
            event.preventDefault();
            this.style.cursor = 'pointer';
            refreshFormset();
            if (numForms > 1) {
                const lastForm = formsetForms[formsetForms.length - 1];
                lastForm.classList.add('imminent-removal');
            }
        });

        // Remove imminent-removal class on mouse leave
        removeFormButton.addEventListener('mouseleave', function (event) {
            event.preventDefault();
            this.style.cursor = 'default';
            refreshFormset();
            const lastForm = formsetForms[formsetForms.length - 1];
            lastForm.classList.remove('imminent-removal');
        });

        // Insert one more form on click
        addFormButton.addEventListener('click', function (event) {
            event.preventDefault();
            refreshFormset();

            if (numForms < maxForms) {
                const lastForm = formsetForms[formsetForms.length - 1];
                const newForm = lastForm.cloneNode(true);

                // The formset number is zero-based, so we can use the current length as the form number
                const formNumber = formsetForms.length;
                newForm.innerHTML = newForm.innerHTML.replace(formRowRegex, `${prefix}-${formNumber}-`);

                // Insert the new form after the last form
                lastForm.parentNode.insertBefore(newForm, lastForm.nextSibling);
            }

            refreshFormset();
            refreshButtonState();
        });
    }

    /***************************************************************************
     * Dialog Box Setup
     **************************************************************************/

    var rightsDialog = undefined
    var sourceRolesDialog = undefined
    var sourceTypesDialog = undefined

    rightsDialog = $('#rights-dialog').dialog({
        autoOpen: false,
        modal: false,
        width: 500,
        position: { my: "center", at: "top", of: window },
        buttons: [
            {
                text: "OK",
                click: () => { rightsDialog.dialog("close") }
            }
        ],
    })

    $('#show-rights-dialog').on("click", (event) => {
        event.preventDefault()
        rightsDialog.dialog("open")
        rightsDialog.dialog("moveToTop")
    })

    sourceRolesDialog = $('#source-roles-dialog').dialog({
        autoOpen: false,
        modal: false,
        width: 500,
        position: { my: "center", at: "top", of: window },
        buttons: [
            {
                text: "OK",
                click: () => { sourceRolesDialog.dialog("close") }
            }
        ],
    })

    $('#show-source-roles-dialog').on("click", (event) => {
        event.preventDefault()
        sourceRolesDialog.dialog("open")
        sourceRolesDialog.dialog("moveToTop")
    })

    sourceTypesDialog = $('#source-types-dialog').dialog({
        autoOpen: false,
        modal: false,
        width: 500,
        position: { my: "center", at: "top", of: window },
        buttons: [
            {
                text: "OK",
                click: () => { sourceTypesDialog.dialog("close") }
            }
        ],
    })

    $('#show-source-types-dialog').on("click", (event) => {
        event.preventDefault()
        sourceTypesDialog.dialog("open")
        sourceTypesDialog.dialog("moveToTop")
    })

    addNewGroupDialog = $('#add-new-group-dialog').dialog({
        autoOpen: false,
        modal: true,
        width: 700,
        position: { my: "center", at: "center", of: window },
    })

    $('#show-add-new-group-dialog').on("click", (event) => {
        event.preventDefault()
        addNewGroupDialog.dialog("open")
        addNewGroupDialog.dialog("moveToTop")
    })

    /***************************************************************************
     * Expandable Forms Setup
    **************************************************************************/

    setupSelectOtherToggle(['#id_contactinfo-other_province_or_state'], removeOther);

    setupSelectOtherToggle(['.rights-select-other'], removeOther);

    setupSelectOtherToggle(['.source-type-select-other'], removeOther);
    setupSelectOtherToggle(['.source-role-select-other'], removeOther);

    // Add a new click handler (with namespace) to fix the event handlers that were cloned.
    $('.add-form-row', '#transfer-form').on('click.transfer-form', (event) => {
        setupSelectOtherToggle(['.rights-select-other'], removeOther);
    })

    /***************************************************************************
     * Group Description Display
    **************************************************************************/
    // Add a change event listener to the group selection field
    if (typeof ID_SUBMISSION_GROUP_SELECTION !== 'undefined') {
        const selectField = $('#' + ID_SUBMISSION_GROUP_SELECTION);
        selectField.on('change', updateGroupDescription);
        initializeGroupTransferForm();
    }

    /***************************************************************************
     * New Group Creation Submission
    **************************************************************************/
    if (typeof MODAL_MODE !== 'undefined' && MODAL_MODE) {
        initializeModalMode();
    }
})


$(() => {
    $(document).ready(function () {
        $("button.close[data-dismiss=alert]").on("click", function (evt) {
            $(evt.currentTarget).parents(".alert-dismissible").hide();
        });
    });
})
