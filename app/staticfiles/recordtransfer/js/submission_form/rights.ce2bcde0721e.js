import { setupFormset } from "./formset";
import { setupSelectOtherToggle } from "./otherField";

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
    });
}
