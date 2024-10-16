document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("form");
    if (!form) {
        console.error("Form element not found");
        return;
    }

    const saveButton = form.querySelector("button[type='submit']");
    const inputFields = form.elements;
    const initialValues = Array.from(inputFields).map(input => {
        // Store initial values of text inputs and the checked state of checkboxes
        if (input.type === "checkbox") {
            return input.checked;
        }
        return input.value;
    });

    function checkForChanges() {
        const hasChanged = Array.from(inputFields).some((input, index) => {
            if (input.type === "checkbox") {
                return input.checked !== initialValues[index];
            }
            return input.value !== initialValues[index];
        });
        saveButton.disabled = !hasChanged;
    }

    Array.from(inputFields).forEach(input => {
        input.addEventListener(input.type === "checkbox" ? "change" : "input", checkForChanges);
    });

    checkForChanges();
});