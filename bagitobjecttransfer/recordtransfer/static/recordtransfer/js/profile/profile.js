document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("form");
    if (!form) {
        console.error("Form element not found");
        return;
    }

    const saveButton = form.querySelector("button[type='submit']");
    const inputFields = form.querySelectorAll("input");

    // Store initial values of input fields
    const initialValues = Array.from(inputFields).map(input => input.value);

    function checkForChanges() {
        const hasChanged = Array.from(inputFields).some((input, index) => input.value !== initialValues[index]);
        saveButton.disabled = !hasChanged;
    }

    // Add event listeners to input fields
    inputFields.forEach(input => {
        input.addEventListener("input", checkForChanges);
    });

    // Initial check to disable the button if no changes
    checkForChanges();
});