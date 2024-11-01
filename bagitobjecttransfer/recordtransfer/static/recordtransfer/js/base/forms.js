/**
 * Functions and configuration for Django forms.
 *
 * Credit to this article for adding/removing forms from formsets:
 * https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
 */


const VALID_INPUTS = 'input:not([type=button]):not([type=submit]):not([type=reset]), textarea, select'
const ID_NUM_REGEX = new RegExp('-(\\d+)-')

let groupDescriptions = {};

/**
 * Test if an element exists on the page.
 * @param {String} selector A jQuery type selector string
 * @returns {Boolean} true if element exists, false otherwise
 */
function elementExists(selector) {
    return $(selector).length !== 0
}

/**
 * Get the prefix name of the currently activated formset.
 * @returns {String} The name of the formset
 */
function getFormPrefix() {
    if (elementExists('#id_rights-TOTAL_FORMS')) {
        return 'rights'
    }
    else if (elementExists('#id_otheridentifiers-TOTAL_FORMS')) {
        return 'otheridentifiers'
    }
    else {
        return 'none'
    }
}

/**
 * Get the current number of forms displayed on the page.
 * @param {String} prefix The form prefix, if it is known
 * @returns {Number} The current number of forms
 */
function getTotalForms(prefix = null) {
    var formPrefix = prefix === null ? getFormPrefix() : prefix
    return parseInt($(`#id_${formPrefix}-TOTAL_FORMS`).val())
}

/**
 * Get the maximum number of allowable forms set by the backend.
 * @param {String} prefix The form prefix, if it is known
 * @returns {Number} The maximum number of forms
 */
function getMaxForms(prefix = null) {
    var formPrefix = prefix === null ? getFormPrefix() : prefix
    return parseInt($(`#id_${formPrefix}-MAX_NUM_FORMS`).val())
}

/**
 * Add a new form to the formset by cloning the selected form. The cloned form is inserted in the
 * document tree directly below the form that was cloned. This function respects whether the
 * max_num of formsets was set in the backend.
 * @param {String} cloneFormSelector The form to clone to create a new form from
 */
function appendNewForm(cloneFormSelector) {
    var prefix = getFormPrefix()
    var totalForms = getTotalForms(prefix)
    var maxNumForms = getMaxForms(prefix)

    if (totalForms + 1 > maxNumForms) {
        alert(`You may not exceed ${maxNumForms} form sections.`)
        return
    }

    var newForm = $(cloneFormSelector).clone(true)
    newForm.addClass('margin-top-25px')
    incrementInputAttributes(newForm)
    incrementLabelAttributes(newForm)
    $(`#id_${prefix}-TOTAL_FORMS`).val(totalForms + 1);
    $(cloneFormSelector).after(newForm);
}

/**
 * Increment all of the indices for the input elements of a formset form
 * @param form The form row element selected by jQuery
 */
function incrementInputAttributes(form) {
    var formIdNumber = -1
    var oldNumber = null
    var newNumber = null

    $(form).find(VALID_INPUTS).each((_, element) => {
        var name = $(element).attr('name')

        if (formIdNumber === -1) {
            var match = ID_NUM_REGEX.exec(name)
            formIdNumber = parseInt(match[1])
            oldNumber = `-${formIdNumber}-`
            newNumber = `-${formIdNumber + 1}-`
        }

        var newName = name.replace(oldNumber, newNumber)
        var newId = `id_${newName}`

        $(element).attr({
            'name': newName,
            'id': newId
        })
            .val('')
            .removeAttr('checked')
    })
}

/**
 * Increment all of the indices for the label elements of a formset form
 * @param form The form row element selected by jQuery
 */
function incrementLabelAttributes(form) {
    var formIdNumber = -1
    var oldNumber = null
    var newNumber = null

    $(form).find('label').each((_, element) => {
        var forValue = $(element).attr('for')

        if (forValue) {
            if (formIdNumber === -1) {
                var match = ID_NUM_REGEX.exec(forValue)
                formIdNumber = parseInt(match[1])
                oldNumber = `-${formIdNumber}-`
                newNumber = `-${formIdNumber + 1}-`
            }

            var newForValue = forValue.replace(oldNumber, newNumber)
            $(element).attr({
                'for': newForValue
            })
        }
    })
}

/**
 * Delete a specific form element from the formset
 * @param {String} deleteFormSelector The selector for the form row
 */
function deleteForm(deleteFormSelector) {
    var prefix = getFormPrefix()
    var total = getTotalForms(prefix)

    if (total > 1) {
        $(deleteFormSelector).remove()

        var forms = $('.form-row')
        $(`#id_${prefix}-TOTAL_FORMS`).val(forms.length)

        // Update each input's index for the remaining forms
        for (var i = 0; i < forms.length; i++) {
            $(forms.get(i)).find(':input').each((_, element) => {
                updateElementIndex(element, i, prefix);
            });
        }
    }
}

/**
 * Update a form element's index within the current form.
 * @param element An element selected from the page with jQuery
 * @param {Number} index The new index the element is to have
 */
function updateElementIndex(element, index, prefix) {
    var idRegex = new RegExp(`(${prefix}-\\d+)`);
    var replacement = prefix + '-' + index;

    forValue = $(element).attr("for")
    if (forValue) {
        const new_for = forValue.replace(idRegex, replacement)
        $(element).attr({
            "for": new_for
        })
    }

    if (element.id) {
        element.id = element.id.replace(idRegex, replacement)
    }

    if (element.name) {
        element.name = element.name.replace(idRegex, replacement)
    }
}

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
const checkGroupChange = () => {
    const groupDescription = document.getElementById(ID_DISPLAY_GROUP_DESCRIPTION);
    const selectedGroupId = document.getElementById(ID_SUBMISSION_GROUP_SELECTION).value;
    let description = groupDescriptions[selectedGroupId];
    if (!description) {
        description = "No description available";
    }
    groupDescription.textContent = description;
}

/**
 * Asynchronously update the group options in the submission group selection dropdown
 * after a new submission group is created.
 */
function populateGroupOptions() {
    $.ajax({
        url: fetchUsersGroupsUrl,
        success: function (groups) {
            const selectField = $('#' + ID_SUBMISSION_GROUP_SELECTION);
            selectField.empty();
            groups.forEach(function (group) {
                selectField.append(new Option(group.name, group.uuid));
                groupDescriptions[group.uuid] = group.description;
            });
            selectField.val(groups[groups.length - 1].uuid).change();
        },
        error: function () {
            alert('Failed to update group options.');
        }
    });
}

$(() => {

    var rightsDialog = undefined
    var sourceRolesDialog = undefined
    var sourceTypesDialog = undefined


    /***************************************************************************
     * Formset Setup
     **************************************************************************/

    var totalForms = getTotalForms()
    $('.remove-form-row').prop('disabled', Boolean(totalForms <= 1))

    $('.add-form-row').on('click', (event) => {
        event.preventDefault()
        appendNewForm('.form-row:last')
        totalForms = getTotalForms()
        $('.remove-form-row').prop('disabled', Boolean(totalForms <= 1))
    })

    $('.remove-form-row').on('click', (event) => {
        event.preventDefault()
        deleteForm('.form-row:last')
        totalForms = getTotalForms()
        $('.remove-form-row').prop('disabled', Boolean(totalForms <= 1))
    })

    $('.remove-form-row').hover(() => {
        totalForms = getTotalForms()
        if (totalForms > 1) {
            $('.form-row:last').find('label').each((_, element) => {
                $(element).addClass('red-text-strikethrough')
            })
            $('.form-row:last').find(VALID_INPUTS).each((_, element) => {
                $(element).addClass('red-border')
                $(element).addClass('red-text-strikethrough')
            })
        }
    }, () => {
        $('.form-row:last').find('label').each((_, element) => {
            $(element).removeClass('red-text-strikethrough')
        })
        $('.form-row:last').find(VALID_INPUTS).each((_, element) => {
            $(element).removeClass('red-border')
            $(element).removeClass('red-text-strikethrough')
        })
    })


    /***************************************************************************
     * Dialog Box Setup
     **************************************************************************/

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
    populateGroupOptions();
    const groupSelectionInput = document.getElementById(ID_SUBMISSION_GROUP_SELECTION);
    groupSelectionInput.addEventListener('change', checkGroupChange);
    checkGroupChange();

    /***************************************************************************
     * New Group Creation Submission
    **************************************************************************/
    $('#submission-group-form').off('submit').on('submit', function (event) {
        event.preventDefault();

        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: $(this).serialize(),
            success: function (response) {
                populateGroupOptions();
                $('#add-new-group-dialog').dialog("close");
            },
            error: function (response) {
                alert(response.responseJSON.message);
            }
        });
    });
})


$(() => {
    $(document).ready(function () {
        $("button.close[data-dismiss=alert]").on("click", function (evt) {
            $(evt.currentTarget).parents(".alert-dismissible").hide();
        });
    });
})
