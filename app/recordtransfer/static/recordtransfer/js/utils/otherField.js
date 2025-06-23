/**
 * Conditionally hides/shows an "other" field based on a select field's value. Adds or removes the
 * .hidden class to the other field's parent to show/hide the element.
 * @param {string} selectFieldInputId The ID of the select element
 * @param {string} otherFieldInputId The ID of the input to conditionally show
 * @param {string|number} otherValue The value of the select element needed to show the other
 * element
 */
export function setupSelectOtherToggle(selectFieldInputId, otherFieldInputId, otherValue) {
    const selectField = document.getElementById(selectFieldInputId);
    const otherInput = document.getElementById(otherFieldInputId);

    if (!selectField || !otherInput) {
        return;
    }

    updateOtherFieldVisibility(selectField, otherInput, otherValue);

    // Update other element when the select field changes
    selectField.addEventListener("change", function () {
        updateOtherFieldVisibility(selectField, otherInput, otherValue);
    });
}

/**
 * Helper function to show/hide an "other" field based on the value of a select field.
 * @param {HTMLSelectElement} selectField - The select element that triggers the visibility change
 * @param {HTMLInputElement} otherInput - The "Other" input field element to show/hide
 * @param {string|number} otherValue - The select option value that should trigger showing the
 * "Other" field
 */
const updateOtherFieldVisibility = (selectField, otherInput, otherValue) => {
    if (!otherInput) {
        return;
    }
    const shouldShow = selectField.value === String(otherValue);
    otherInput.parentElement.classList.toggle("hidden", !shouldShow);
    otherInput.required = shouldShow;
};