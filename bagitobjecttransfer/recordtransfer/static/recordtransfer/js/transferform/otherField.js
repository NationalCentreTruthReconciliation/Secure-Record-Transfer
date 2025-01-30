/**
 * Conditionally hides/shows an "other" field based on a select field's value. Adds or removes the
 * .hidden-item class to the other field's parent to show/hide the element.
 * @param {string} selectFieldInputId The ID of the select element
 * @param {string} otherFieldInputId The ID of the input to conditionally show
 * @param {string} otherValue The value of the select element needed to show the other element
 */
export function setupSelectOtherToggle(selectFieldInputId, otherFieldInputId, otherValue) {
    const selectField = document.getElementById(selectFieldInputId);

    // Hide element at first (if needed)
    if (selectField.value != otherValue) {
        const otherInput = document.getElementById(otherFieldInputId);

        if (otherInput) {
            const container = otherInput.parentElement;
            container.classList.add("hidden-item");
        }
    }

    // Update other element when the select field changes
    selectField.addEventListener("change", function (event) {
        const otherInput = document.getElementById(otherFieldInputId);

        if (!otherInput) {
            return;
        }

        const container = otherInput.parentElement;

        if (this.value == otherValue) {
            container.classList.remove("hidden-item");
        }
        else {
            container.classList.add("hidden-item");
        }
    });
}
