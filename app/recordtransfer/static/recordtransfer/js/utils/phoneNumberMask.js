import IMask from "imask";

/**
 * Sets up phone number input masking for form fields.
 * Applies a phone number mask format "+0 (000) 000-0000" to all input elements
 * with IDs ending in "-phone_number".
 */
export function setupPhoneNumberMask() {
    // Find all phone number input fields
    const phoneInputs = document.querySelectorAll(
        "input[id$=\"phone_number\"]"
    );

    phoneInputs.forEach(input => {
        // Create IMask instance for phone number
        IMask(input, {
            mask: "+0 (000) 000-0000",
            lazy: false, // Show mask immediately
            placeholderChar: "_"
        });
    });
}
