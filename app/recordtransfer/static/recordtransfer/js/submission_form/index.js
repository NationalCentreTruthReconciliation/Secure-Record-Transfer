/* global singleCaptchaFn */
import { setupHelpTooltips } from "../base/tooltip";
import { setupContactInfoForm } from "./contactInfo";
import { setupOtherIdentifiersForm } from "./otherIdentifiers";
import { setupRightsForm } from "./rights";
import { setupSourceInfoForm } from "./sourceInfo";
import { setupSubmissionGroupForm } from "./submissionGroup";
import { setupUnsavedChangesProtection } from "./unsavedChanges";
import { setupUppy } from "./uppyForm";
import {
    setupDatePickers,
    setupInputMasks,
} from "./widgets";

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
};

export const initializeSubmissionForm = () => {
    setupDatePickers();
    setupInputMasks();
    setupUnsavedChangesProtection();
    setupHelpTooltips();

    _setupWithContext();

    window.addEventListener("popstate", (event) => {
        if (event.state && event.state.step) {
            showStep(event.state.step);
        }
    });
    const showStep = (stepNumber) => {
    // Navigate to the specific step
        const stepButton = document.querySelector(
            `button[name="wizard_goto_step"][value="${stepNumber}"]`
        );
        if (stepButton) {
            stepButton.click();
        } else {
        // Fallback: use form submission to navigate to step
            const form = document.getElementById("submission-form");
            if (form) {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = "wizard_goto_step";
                input.value = stepNumber;
                form.appendChild(input);
                form.submit();
            }
        }
    };

    const submitButton = document.getElementById("submit-form-btn");
    if (submitButton) {
        submitButton.addEventListener("click", (event) => {
            event.preventDefault(); // Prevent form submission
            singleCaptchaFn(); // Let reCAPTCHA handle the submission after validation
        });
    }
};
