import { setupSelectOtherToggle } from "./otherField";

/**
 * Sets up the rights form.
 */
export function setupRightsForm() {
    const contextElement = document.getElementById("py_context_rights");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    setupSelectOtherToggle(
        context["id_rights_type"],
        context["id_other_rights_type"],
        context["other_rights_type_id"]
    );
}
