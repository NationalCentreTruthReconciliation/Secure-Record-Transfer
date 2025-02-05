/**
 * Conditionally hides/shows an "other" field based on a select field's value. Adds or removes the
 * .hidden-item class to the other field's parent to show/hide the element.
 * @param {string} selectFieldInputId The ID of the select element
 * @param {string} otherFieldInputId The ID of the input to conditionally show
 * @param {string} otherValue The value of the select element needed to show the other element
 */
export function setupSelectOtherToggle(selectFieldInputId, otherFieldInputId, otherValue) {
    const selectField = document.getElementById(selectFieldInputId);
    const otherInput = document.getElementById(otherFieldInputId);

    updateOtherFieldVisibility(selectField, otherInput, otherValue);

    // Update other element when the select field changes
    selectField.addEventListener("change", function () {
        updateOtherFieldVisibility(selectField, otherInput, otherValue);
    });
}

const updateOtherFieldVisibility = (selectField, otherInput, otherValue) => {
    if (!otherInput) {
        return;
    }
    const shouldShow = Number(selectField.value) === Number(otherValue);
    otherInput.parentElement.classList.toggle("hidden-item", !shouldShow);
};