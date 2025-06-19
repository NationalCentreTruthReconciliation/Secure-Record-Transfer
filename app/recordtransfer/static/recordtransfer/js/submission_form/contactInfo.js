import { setupSelectOtherToggle } from "../utils/otherField";

/**
 * Sets up the contact info form.
 * @param {object} context - The form context containing references to form elements.
 */
export function setupContactInfoForm(context) {
    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_value"]
    );
}
