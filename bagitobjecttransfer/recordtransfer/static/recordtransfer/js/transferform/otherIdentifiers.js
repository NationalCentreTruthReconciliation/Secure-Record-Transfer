import { setupFormset } from "./formset";

/**
 * Sets up the other identifiers form.
 */
export function setupOtherIdentifiersForm() {
    const contextElement = document.getElementById("py_context_otheridentifiers");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);

    const formsetPrefix = context["formset_prefix"];
    const numExtraForms = context["num_extra_forms"];

    setupFormset(formsetPrefix, numExtraForms);
}
