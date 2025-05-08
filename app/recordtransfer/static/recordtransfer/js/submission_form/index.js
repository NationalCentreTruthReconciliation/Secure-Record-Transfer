/* global singleCaptchaFn */
import "../../css/submission_form/review_step.css";
import "../../css/submission_form/uppy.css";

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
    setupHelpTooltips,
} from "./widgets";

const _setupWithContext = () => {
    const contextElement = document.getElementById("py_context");
    if (!contextElement) {
        return;
    }
    const context = JSON.parse(contextElement.textContent);
    const context_id = context["context_id"];
    
    switch (context_id) {
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

const setup = () => {
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

document.addEventListener("DOMContentLoaded", setup);

// Re-setup the form when HTMX swaps the main container
document.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id === "main-container") {
        setup();
    }
});