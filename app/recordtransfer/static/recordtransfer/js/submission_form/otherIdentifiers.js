import { setupHelpTooltips } from "../base/tooltip.js";
import { setupFormset } from "./formset.js";

/**
 * Sets up the other identifiers form.
 * @param {object} context - The context object containing form configuration
 */
export function setupOtherIdentifiersForm(context) {
    const formsetPrefix = context["formset_prefix"];
    // Set up tooltips for all initial formset rows
    setupHelpTooltips();

    // Set up tooltips for new rows
    setupFormset(formsetPrefix, () => {
        setupHelpTooltips();
    });
}
