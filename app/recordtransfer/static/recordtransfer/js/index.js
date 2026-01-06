import "../css/main.css";

import "../css/base/banner.css";
import "../css/base/base.css";
import "../css/base/footer.css";
import "../css/base/home.css";
import "../css/base/navbar.css";
import "../css/base/submission_form.css";
import "../css/base/tooltip.css";
import "../css/base/widget.css";
import "../css/base/accounts.css";

import "../css/submission_form/review_step.css";
import "../css/submission_form/uppy.css";

import "htmx-ext-head-support";
import htmx from "htmx.org";

import { setupMessages } from "./base/messages.js";
import { setupNavbar } from "./base/navbar.js";
import { setupHelpTooltips } from "./base/tooltip.js";
import { initializeProfile } from "./profile/index.js";
import {
    setupRegistrationFormValidation,
    setupLoginFormValidation,
    setupPasswordResetFormValidation,
} from "./registration/form-validation.js";
import { initializeSessionLimitPage } from "./session_limit/index.js";
import { initializeSubmissionForm } from "./submission_form/index.js";
import { initializeSubmissionGroup } from "./submission_group/index.js";
import { initializeCustomModalEvents, setupBaseHtmxEventListeners } from "./utils/htmx.js";
import { setupToastNotifications, displayStoredToast } from "./utils/toast.js";


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
