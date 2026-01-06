/* global singleCaptchaFn */
import { setupHelpTooltips } from "../base/tooltip.js";
import { setupContactInfoForm } from "./contactInfo.js";
import { setupOtherIdentifiersForm } from "./otherIdentifiers.js";
import { setupRightsForm } from "./rights.js";
import { setupSourceInfoForm } from "./sourceInfo.js";
import { setupSubmissionGroupForm } from "./submissionGroup.js";
import { setupUnsavedChangesProtection } from "./unsavedChanges.js";
import { setupUppy } from "./uppyForm.js";
import {
    setupDatePickers,
    setupInputMasks,
} from "./widgets.js";

const _setupWithContext = () => {
    const contextElement = document.querySelector("[id^=\"js_context_\"]");
    if (!contextElement) {
        return;
    }
    const context = JSON.parse(contextElement.textContent);
    const contextFor = contextElement.id.replace(/^js_context_/, "");

    switch (contextFor) {
        case "contactinfo":
            setupContactInfoForm(context);
            break;
        case "sourceinfo":
            setupSourceInfoForm(context);
            break;
        case "rights":
            setupRightsForm(context);

            break;
        case "otheridentifiers":
            setupOtherIdentifiersForm(context);
            break;
        case "groupsubmission":
            setupSubmissionGroupForm(context);
            break;
        case "uploadfiles":
            setupUppy(context);
            break;
        default:
            break;
    }

    setupSubmitButton(context);
};

/**
 * Setup submit button behavior based on reCAPTCHA configuration
 * @param {object} context - Configuration context
 */
const setupSubmitButton = (context) => {
    if (!context.RECAPTCHA_ENABLED) {
        return;
    }
    const submitButton = document.getElementById("submit-form-btn");

    if (!submitButton) {
        return;
    }
    submitButton.addEventListener("click", (event) => {
        event.preventDefault();
        singleCaptchaFn(); // Let reCAPTCHA handle the submission after validation
    });
};

export const initializeSubmissionForm = () => {
    setupDatePickers();
    setupInputMasks();
    setupUnsavedChangesProtection();
    setupHelpTooltips();

    _setupWithContext();
};
