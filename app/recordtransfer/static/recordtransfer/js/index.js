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

import { setupMessages } from "./base/messages";
import { setupNavbar } from "./base/navbar";
import { setupHelpTooltips } from "./base/tooltip";
import { initializeProfile } from "./profile/index";
import {
    setupRegistrationFormValidation,
    setupLoginFormValidation,
    setupPasswordResetFormValidation,
} from "./registration/form-validation";
import { initializeSessionLimitPage } from "./session_limit/index";
import { initializeSubmissionForm } from "./submission_form/index";
import { initializeSubmissionGroup } from "./submission_group/index";
import { initializeCustomModalEvents, setupBaseHtmxEventListeners } from "./utils/htmx";
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
