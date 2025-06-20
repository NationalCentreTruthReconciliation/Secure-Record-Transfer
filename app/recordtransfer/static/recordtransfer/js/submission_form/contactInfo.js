import { setupSelectOtherToggle } from "../utils/otherField";

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
        console.error("Save contact info modal not found.");
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

    modal.showModal();
};