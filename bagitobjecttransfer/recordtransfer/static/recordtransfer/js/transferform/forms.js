import { setupContactInfoForm } from "./contactInfo";
import { setupFormset } from "./formset";
import { setupRightsForm } from "./rights";
import { setupSourceInfoForm } from "./sourceInfo";
import { setupSubmissionGroupForm } from "./submissionGroup";
import { setupUppy } from "./uppyForm";

document.addEventListener("DOMContentLoaded", function () {
    setupFormset();

    setupContactInfoForm();
    setupSourceInfoForm();
    setupRightsForm();
    setupSubmissionGroupForm();
    setupUppy();

    const submitButton = document.getElementById("submit-form-btn");
    if (submitButton) {
        submitButton.addEventListener("click", () => {
            singleCaptchaFn();
        });
    }
});
