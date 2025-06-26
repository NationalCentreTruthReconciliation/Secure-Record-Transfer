import { setupSelectOtherToggle } from "../utils/otherField";
import { setupHelpTooltips } from "../base/tooltip";
import { setupFormset } from "./formset";

/**
 * Sets up the rights form.
 * @param {object} context - The context object containing form configuration
 */
export function setupRightsForm(context) {
    const formsetPrefix = context["formset_prefix"];

    // Set up the formset, and setup the select other toggle when a new form is added.
    setupFormset(formsetPrefix, newForm => {
        const selectElement = newForm.querySelector("[id$=\"-rights_type\"]");
        const index = selectElement.id.match(/\d+/)[0];
        setupSelectOtherToggle(
            selectElement.id,
            `id_rights-${index}-other_rights_type`,
            context["other_rights_type_id"],
        );

        setupRightsNoteToggle(
            selectElement.id,
            `id_rights-${index}-rights_value`
        );

        setupHelpTooltips();

        // Reset the selected value upon form creation
        selectElement.value = "";
        selectElement.dispatchEvent(new Event("change"));
    });

    document.querySelectorAll("[id$=\"-rights_type\"]").forEach(element => {
        const index = element.id.match(/\d+/)[0];
        setupSelectOtherToggle(
            element.id,
            `id_rights-${index}-other_rights_type`,
            context["other_rights_type_id"],
        );

        // Setup notes toggle for this specific form
        setupRightsNoteToggle(
            element.id,
            `id_rights-${index}-rights_value`
        );
    });
}

/**
 * Sets up toggling the visibility of the rights value field based on the value of
 * the rights type field with the same index.
 * @param {string} rightsTypeId - The ID of the rights type select element.
 * @param {string} rightsValueId - The ID of the rights value textarea element.
 */
function setupRightsNoteToggle(rightsTypeId, rightsValueId) {
    const rightsTypeField = document.getElementById(rightsTypeId);
    const rightsValueField = document.getElementById(rightsValueId);
    const formContainer = rightsValueField ? rightsValueField.closest(".flex-item") : null;

    /**
     * Updates the visibility of the rights value field based on whether
     * the rights type field has a value.
     */
    function updateVisibility() {
        if (rightsTypeField && rightsTypeField.value) {
            if (formContainer) {formContainer.style.display = "";}
        } else {
            if (formContainer) {formContainer.style.display = "none";}
        }
    }

    // Add event listener for the rights type field
    if (rightsTypeField) {
        rightsTypeField.addEventListener("change", updateVisibility);
    }

    updateVisibility();
}