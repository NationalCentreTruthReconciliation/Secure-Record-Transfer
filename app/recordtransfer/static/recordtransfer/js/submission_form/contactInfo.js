import { setupSelectOtherToggle } from "./otherField";

/**
 * Sets up the contact info form.
 */
export function setupContactInfoForm(context) {
    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_id"]
    );
}
