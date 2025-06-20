/**
 * Sets up form change tracking to enable/disable the save button
 * @param {HTMLFormElement} form - The form element to track
 * @param {HTMLButtonElement} saveButton - The save button to enable/disable
 */
export function setupFormChangeTracking(form, saveButton) {
    // Store initial form values
    const initialValues = new Map();
    const formElements = form.querySelectorAll("input, textarea, select");

    // Capture initial values
    formElements.forEach(element => {
        if (element.type === "checkbox" || element.type === "radio") {
            initialValues.set(element.name, element.checked);
        } else {
            initialValues.set(element.name, element.value || "");
        }
    });

    /**
     * Check if any form values have changed from their initial state
     * @returns {boolean} - True if any field has been modified
     */
    function hasFormChanged() {
        for (const element of formElements) {
            let currentValue;
            if (element.type === "checkbox" || element.type === "radio") {
                currentValue = element.checked;
            } else {
                currentValue = element.value || "";
            }

            const initialValue = initialValues.get(element.name);

            if (currentValue !== initialValue) {
                return true;
            }
        }
        return false;
    }

    /**
     * Update the save button state based on form changes
     */
    function updateSaveButtonState() {
        const hasChanged = hasFormChanged();
        saveButton.disabled = !hasChanged;

        if (hasChanged) {
            saveButton.classList.remove("btn-disabled");
        } else {
            saveButton.classList.add("btn-disabled");
        }
    }

    // Add event listeners to all form elements
    formElements.forEach(element => {
        const events = ["input", "change"];
        events.forEach(eventType => {
            element.addEventListener(eventType, updateSaveButtonState);
        });
    });

    // Initial check
    updateSaveButtonState();
}