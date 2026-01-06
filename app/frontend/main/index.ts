import "./css/tailwind.css";

import "./css/base/banner.css";
import "./css/base/base.css";
import "./css/base/footer.css";
import "./css/base/home.css";
import "./css/base/navbar.css";
import "./css/base/submission_form.css";
import "./css/base/tooltip.css";
import "./css/base/widget.css";
import "./css/base/accounts.css";

import "./css/submission_form/review_step.css";
import "./css/submission_form/uppy.css";

import "htmx-ext-head-support";
import htmx from "htmx.org";

import { setupMessages } from "./js/base/messages.js";
import { setupNavbar } from "./js/base/navbar.js";
import { setupHelpTooltips } from "./js/base/tooltip.js";
import { initializeProfile } from "./js/profile/index.js";
import {
    setupRegistrationFormValidation,
    setupLoginFormValidation,
    setupPasswordResetFormValidation,
} from "./js/registration/form-validation.js";
import { initializeSessionLimitPage } from "./js/session_limit/index.js";
import { initializeSubmissionForm } from "./js/submission_form/index.js";
import { initializeSubmissionGroup } from "./js/submission_group/index.js";
import { initializeCustomModalEvents, setupBaseHtmxEventListeners } from "./js/utils/htmx.js";
import { setupToastNotifications, displayStoredToast } from "./js/utils/toast.js";

declare global {
    interface Window {
        htmx: unknown;
    }
}

window.htmx = htmx;

document.addEventListener("DOMContentLoaded", () => {
    setupBaseHtmxEventListeners();
    initializeCustomModalEvents();
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
