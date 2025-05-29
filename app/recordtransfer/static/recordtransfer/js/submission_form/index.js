/* global singleCaptchaFn */
import "../../css/submission_form/review_step.css";
import "../../css/submission_form/uppy.css";
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

export const setup = () => {
    setupDatePickers();
    setupInputMasks();
    setupUnsavedChangesProtection();
    setupHelpTooltips();

    _setupWithContext();

    const submitButton = document.getElementById("submit-form-btn");
    if (submitButton) {
        submitButton.addEventListener("click", () => {
            singleCaptchaFn();
        });
    }
};
