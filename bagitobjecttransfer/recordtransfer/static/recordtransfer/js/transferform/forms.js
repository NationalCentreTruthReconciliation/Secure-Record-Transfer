/**
 * Functions and configuration for Django forms.
 *
 * Credit to this article for adding/removing forms from formsets:
 * https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
 */

import { setupSubmissionGroupModal } from "./submissionGroupModal";

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
 * Conditionally hides/shows an "other" field based on a select field's value. Adds or removes the
 * .hidden-item class to the other field's parent to show/hide the element.
 *
 * @param selectFieldInputId The ID of the select element
 * @param otherFieldInputId The ID of the input to conditionally show
 * @param otherValue The value of the select element needed to show the other element
 */
function setupSelectOtherToggle2(selectFieldInputId, otherFieldInputId, otherValue) {
    const selectField = document.getElementById(selectFieldInputId);

    // Hide element at first (if needed)
    if (selectField.value != otherValue) {
        const otherInput = document.getElementById(otherFieldInputId);

        if (otherInput) {
            const container = otherInput.parentElement;
            container.classList.add("hidden-item");
        }
    }

    // Update other element when the select field changes
    selectField.addEventListener("change", function (event) {
        const otherInput = document.getElementById(otherFieldInputId);

        if (!otherInput) {
            return;
        }

        const container = otherInput.parentElement;

        if (this.value == otherValue) {
            container.classList.remove("hidden-item");
        }
        else {
            container.classList.add("hidden-item");
        }
    });
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

    setupSubmissionGroupModal();

    /***************************************************************************
     * Expandable Forms Setup
    **************************************************************************/

    setupSelectOtherToggle(['#id_contactinfo-other_province_or_state'], removeOther);

    setupSelectOtherToggle(['.rights-select-other'], removeOther);

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

    /**********************************************************************************************
     * Source information form setup
     *********************************************************************************************/

    // Context passed from template to JS
    const sourceInfoContextElement = document.getElementById("py_context_source_info");

    if (sourceInfoContextElement) {
        const sourceInfoContext = JSON.parse(sourceInfoContextElement.textContent);

        // Toggles Other source type field depending on value of Source type field
        setupSelectOtherToggle2(
            sourceInfoContext["id_source_type"],
            sourceInfoContext["id_other_source_type"],
            sourceInfoContext["other_type_id"]
        );

        // Toggles Other source role field depending on value of Source role field
        setupSelectOtherToggle2(
            sourceInfoContext["id_source_role"],
            sourceInfoContext["id_other_source_role"],
            sourceInfoContext["other_role_id"]
        );

        // Add faux-required-field to labels
        document.querySelectorAll(".faux-required-field").forEach((el) => {
            let label = el.previousElementSibling;
            if (label && label.tagName === "LABEL") {
                label.classList.add("faux-required-field");
            }
        });

        const sourceTypeSelect = document.getElementById(sourceInfoContext["id_source_type"]);
        const sourceRoleSelect = document.getElementById(sourceInfoContext["id_source_role"]);
        const enterManualInfoInputId = sourceInfoContext["id_enter_manual_source_info"];
        const enterManualInfoInputElement = document.getElementById(enterManualInfoInputId);

        if (enterManualInfoInputElement) {
            enterManualInfoInputElement.addEventListener("change", function (event) {
                const selected = this.querySelector("input[type=radio]:checked").value;

                if (selected === "yes") {
                    document.querySelectorAll(".initially-hidden").forEach((el) => {
                        el.classList.remove("hidden-item");
                    });

                    // Dispatch events to update "other" fields if they were just shown by accident
                    sourceTypeSelect.dispatchEvent(new Event("change"));
                    sourceRoleSelect.dispatchEvent(new Event("change"));
                }
                else {
                    document.querySelectorAll(".initially-hidden").forEach((el) => {
                        el.classList.add("hidden-item");
                    });
                }
            });

            enterManualInfoInputElement.dispatchEvent(new Event("change"));
        }
        else {
            console.warn(`No element exists with the id: ${enterManualInfoInputId}`);
        }
    }
})

document.addEventListener("DOMContentLoaded", () => {
    const submitButton = document.getElementById("submit-form-btn");
    if (submitButton) {
        submitButton.addEventListener("click", () => {
            singleCaptchaFn();
        });
    }   
});
