import { setupFormset } from "./formset";
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

    const formsetPrefix = context["formset_prefix"];

    setupFormset(formsetPrefix);

    document.querySelectorAll("[id$=\"-rights_type\"]").forEach(element => {
        const index = element.id.match(/\d+/)[0];
        setupSelectOtherToggle(
            element.id,
            `id_rights-${index}-other_rights_type`,
            context["other_rights_type_id"],
        );
    });
}
