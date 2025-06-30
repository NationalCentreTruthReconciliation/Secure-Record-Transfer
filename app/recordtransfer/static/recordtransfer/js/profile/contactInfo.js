import { setupFormChangeTracking } from "../utils/forms";
import { setupSelectOtherToggle } from "../utils/otherField";

/**
 * Sets up the contact info form.
 * @param {object} context - The form context containing references to form elements.
 */
export function setupUserContactInfoForm(context) {
    const form = document.getElementById("contact-info-form");
    const saveButton = document.getElementById("contact-info-save-btn");

    setupFormChangeTracking(form, saveButton);
    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_value"]
    );
}