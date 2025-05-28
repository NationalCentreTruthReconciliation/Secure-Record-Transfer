import { setupSelectOtherToggle } from "./otherField";

/**
 * Sets up the contact info form.
 * @param {object} context - The form context containing references to form elements.
 */
export function setupContactInfoForm(context) {
    if (
        !context ||
        !context["id_province_or_state"] ||
        !context["id_other_province_or_state"] ||
        !context["other_province_or_state_id"]
    ) {
        return;
    }
    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_id"]
    );
}
