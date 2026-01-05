import {
    setupProfileForm,
    setupSubmissionGroupForm,
    setupAssignSubmissionGroupForm,
} from "../forms/forms.js";
import {
    refreshIPSubmissionTable,
    refreshSubmissionGroupTable,
    refreshSubmissionTable,
} from "../utils/htmx.js";
import { closeModal, showModal } from "../utils/utils.js";
import { setupUserContactInfoForm } from "./contactInfo.js";
import { initTabListeners, restoreTab, redirectToCorrectFragment } from "./tab.js";

/**
 * Main initialization function to set up all profile-related functionality
 */
export const initializeProfile = function() {
    let context = null;
    const contextElement = document.getElementById("py_context_user_profile");

    if (!contextElement) {
        return;
    }

    context = JSON.parse(contextElement.textContent);
    if (!context) {
        console.error("Context not available to set up profile page.");
        return;
    }

    setupProfileForm(context);
    setupUserContactInfoForm(context);
    initTabListeners();
    restoreTab();
    redirectToCorrectFragment();

    document.addEventListener("modal:beforeSwap", (e) => {
        // A server response indicates an unsuccessful form submission
        if (e.detail.serverReponse) {
            return;
        }

        const triggeredBy = e.detail.requestConfig.elt.id;

        if ("submission-group-form" === triggeredBy) {
            e.preventDefault();
            closeModal();
            refreshSubmissionGroupTable(context);
        }

        else if ("assign-submission-group-form" === triggeredBy) {
            e.preventDefault();
            closeModal();
            refreshSubmissionTable(context);
            refreshSubmissionGroupTable(context);
        }
    });

    document.addEventListener("modal:afterSwap", (e) => {
        const triggeredBy = e.detail.requestConfig.elt.id;

        if (triggeredBy === "id_new_submission_group_button") {
            setupSubmissionGroupForm(context);
        } else if (triggeredBy.startsWith("assign_submission_group_")) {
            setupAssignSubmissionGroupForm();
        }

        // Always show the modal
        showModal();
    });

    document.addEventListener("modal:afterInProgressDelete", () => {
        closeModal();
        refreshIPSubmissionTable(context);
    });

    document.addEventListener("modal:afterGroupDelete", () => {
        closeModal();
        refreshSubmissionGroupTable(context);
        refreshSubmissionTable(context);
    });

    document.addEventListener("modal:afterGroupCreate", () => {
        closeModal();
        refreshSubmissionGroupTable(context);
        refreshSubmissionTable(context);
    });

    document.getElementById("account-info-form")?.addEventListener("htmx:afterRequest", () => {
        setupProfileForm(context);
    });

    document.getElementById("contact-info-form")?.addEventListener("htmx:afterRequest", () => {
        setupUserContactInfoForm(context);
    });
};
