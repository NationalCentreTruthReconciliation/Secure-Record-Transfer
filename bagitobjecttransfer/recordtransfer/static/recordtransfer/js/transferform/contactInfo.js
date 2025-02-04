import { setupSelectOtherToggle } from "./otherField";

/**
 * Sets up the contact info form.
 */
export function setupContactInfoForm() {
    const contextElement = document.getElementById("py_context_contactinfo");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_id"]
    );
}
