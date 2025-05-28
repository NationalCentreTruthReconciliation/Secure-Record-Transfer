import { setupFormset } from "./formset";

/**
 * Sets up the other identifiers form.
 * @param {object} context - The context object containing form configuration
 */
export function setupOtherIdentifiersForm(context) {
    if (!context || !context["formset_prefix"]) {
        return;
    }
    const formsetPrefix = context["formset_prefix"];

    setupFormset(formsetPrefix);
}
