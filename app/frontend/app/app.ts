import "htmx-ext-head-support";
import htmx from "htmx.org";

import { setupMessages } from "./js/base/messages.js";
import { setupNavbar } from "./js/base/navbar.js";
import { setupHelpTooltips } from "./js/base/tooltip.js";
import { initializeProfile } from "./js/profile/index";
import {
    setupRegistrationFormValidation,
    setupLoginFormValidation,
    setupPasswordResetFormValidation,
} from "./js/registration/form-validation.js";
import { initializeSessionLimitPage } from "./js/session_limit/index";
import { initializeSubmissionForm } from "./js/submission_form/index";
import { initializeSubmissionGroup } from "./js/submission_group/index";
import { setupBaseHtmxEventListeners } from "./js/utils/htmx.js";
import { setupToastNotifications, displayStoredToast } from "./js/utils/toast.js";

declare global {
    interface Window {
        htmx: unknown;
    }
}

window.htmx = htmx;

document.addEventListener("DOMContentLoaded", () => {
    setupBaseHtmxEventListeners();
    setupNavbar();
    setupMessages();
    setupToastNotifications();
    displayStoredToast();
    setupRegistrationFormValidation();
    setupLoginFormValidation();
    setupPasswordResetFormValidation();
    initializeProfile();
    initializeSubmissionForm();
    initializeSubmissionGroup();
    initializeSessionLimitPage();
});

window.addEventListener("load", () => {
    setupHelpTooltips();
});
