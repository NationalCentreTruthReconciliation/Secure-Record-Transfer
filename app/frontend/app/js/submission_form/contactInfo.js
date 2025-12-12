import { setupSelectOtherToggle } from "../utils/otherField";
import { showErrorToast } from "../utils/toast";

/**
 * Sets up the contact info form.
 * @param {object} context - The form context containing references to form elements.
 */
export function setupContactInfoForm(context) {
    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_value"]
    );
    setupPromptSaveContactInfoListener(context);
}

const setupPromptSaveContactInfoListener = (context) => {
    if (!window.htmx) {
        return;
    }

    window.htmx.on("promptSaveContactInfo", (event) => {
        displaySaveContactInfoModal(event.detail.contactInfo, context);
    });

    // Prevent default swap behavior if response is empty
    window.htmx.on("htmx:beforeSwap", (event) => {
        if (!event.detail.xhr.responseText) {
            event.detail.shouldSwap = false;
        }
    });
};

const displaySaveContactInfoModal = (contactInfo, context) => {
    const modal = document.getElementById("save_contact_info_modal");
    if (!modal) {
        return;
    }

    // Populate modal with contact info data
    const updateModalField = (fieldId, value) => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.textContent = value || "";
        }
    };

    // Handle the case where province_or_state is "Other"
    const provinceOrState = contactInfo.province_or_state !==
        context["other_province_or_state_value"]
        ? contactInfo.province_or_state
        : contactInfo.other_province_or_state;

    updateModalField("modal-phone-number", contactInfo.phone_number);
    updateModalField("modal-address-line-1", contactInfo.address_line_1);
    updateModalField("modal-address-line-2", contactInfo.address_line_2);
    updateModalField("modal-city", contactInfo.city);
    updateModalField("modal-province-or-state",provinceOrState);
    updateModalField("modal-postal-or-zip-code", contactInfo.postal_or_zip_code);
    updateModalField("modal-country", contactInfo.country);

    // Set up button event handlers
    setupModalButtonHandlers(contactInfo, context);

    modal.showModal();
};

const setupModalButtonHandlers = (contactInfo, context) => {
    const continueButton = document.getElementById("modal-continue-without-saving");
    const saveButton = document.getElementById("modal-save-contact-info");
    const modal = document.getElementById("save_contact_info_modal");

    if (!continueButton || !saveButton || !modal) {
        console.error("Modal buttons or modal not found.");
        return;
    }

    // Remove any existing event listeners to prevent duplicates
    const newContinueButton = continueButton.cloneNode(true);
    const newSaveButton = saveButton.cloneNode(true);
    continueButton.parentNode.replaceChild(newContinueButton, continueButton);
    saveButton.parentNode.replaceChild(newSaveButton, saveButton);

    // Continue without saving - just proceed to next step
    newContinueButton.addEventListener("click", () => {
        modal.close();
        proceedToNextStep();
    });

    // Save contact info and then proceed
    newSaveButton.addEventListener("click", () => {
        saveContactInfoAndProceed(contactInfo, context);
    });
};

const proceedToNextStep = () => {
    const nextButton = document.getElementById("form-next-button");
    if (nextButton) {
        nextButton.click();
    }
};

const saveContactInfoAndProceed = (contactInfo, context) => {
    const form = document.getElementById("submission-form");
    if (!form) {
        console.error("Submission form not found.");
        return;
    }

    // Get the URL from context
    const updateUrl = context["account_info_update_url"];
    if (!updateUrl) {
        console.error("Account info update URL not found in context.");
        proceedToNextStep();
        return;
    }

    // Get CSRF token from the form
    const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]");

    // Create data object with contact info
    const requestData = {
        "phone_number": contactInfo.phone_number || "",
        "address_line_1": contactInfo.address_line_1 || "",
        "address_line_2": contactInfo.address_line_2 || "",
        "city": contactInfo.city || "",
        "province_or_state": contactInfo.province_or_state || "",
        "other_province_or_state": contactInfo.other_province_or_state || "",
        "postal_or_zip_code": contactInfo.postal_or_zip_code || "",
        "country": contactInfo.country || ""
    };

    if (csrfToken) {
        requestData.csrfmiddlewaretoken = csrfToken.value;
    }

    // Make HTMX request to save contact info
    window.htmx.ajax("POST", updateUrl, {
        values: requestData,
        swap: "none"
    }).then(() => {
        proceedToNextStep();
    }).catch((error) => {
        showErrorToast(error.message);
        // Still proceed to next step even if save fails
        proceedToNextStep();
    }).finally(() => {
        const modal = document.getElementById("save_contact_info_modal");
        if (modal) {
            modal.close();
        }
    });
};