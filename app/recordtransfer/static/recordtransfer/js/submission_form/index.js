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

document.addEventListener("DOMContentLoaded", function () {
    setupDatePickers();
    setupInputMasks();
    setupUnsavedChangesProtection();

    setupWithContext();

    const submitButton = document.getElementById("submit-form-btn");
    if (submitButton) {
        submitButton.addEventListener("click", () => {
            singleCaptchaFn();
        });
    }
});

const setupWithContext = () => {
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
        setupUppy();
        break;
    default:
        console.log("Unknown context_id:", context_id);
    }
};

window.addEventListener("load", function () {
    setupHelpTooltips();
});

// Function to handle JS context updates after HTMX swaps
document.addEventListener("htmx:afterSwap", function(event) {
    // Check if our target was updated
    if (event.target.id === "py_context_div") {
        // Redo setup
        console.log("Context updated, redoing setup");
        setupWithContext();
    }
});