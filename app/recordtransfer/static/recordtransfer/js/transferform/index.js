/* global singleCaptchaFn */
import "../../css/transferform/review_step.css";
import "../../css/transferform/uppy.css";

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
    setupContactInfoForm();
    setupSourceInfoForm();
    setupRightsForm();
    setupOtherIdentifiersForm();
    setupSubmissionGroupForm();
    setupUnsavedChangesProtection();
    setupUppy();

    const submitButton = document.getElementById("submit-form-btn");
    if (submitButton) {
        submitButton.addEventListener("click", () => {
            singleCaptchaFn();
        });
    }
});

window.addEventListener("load", function () {
    setupHelpTooltips();
});
