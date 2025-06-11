import { setupFormset } from "./formset";

/**
 * Sets up the other identifiers form.
 * @param {object} context - The context object containing form configuration
 */
export function setupOtherIdentifiersForm(context) {
    const formsetPrefix = context["formset_prefix"];

    setupFormset(formsetPrefix);
}
