// The purpose of this script is to allow the server to save the current step's form data
// before navigating to the previous step.
document.addEventListener("DOMContentLoaded", () => {
    if (!previousFormStep) {
        return;
    }

    const previousButton = document.getElementById("form-previous-button");
    const form = document.getElementById("transfer-form");

    previousButton.addEventListener("click", (event) => {
        event.preventDefault();

        // Add the previous button's form value as a hidden input
        const previousFormStepElement = document.createElement("input");
        previousFormStepElement.type = "hidden";
        previousFormStepElement.name = GO_TO_STEP_ACTION;
        previousFormStepElement.value = previousButton.value;
        form.appendChild(previousFormStepElement);

        const saveFormStepElement = document.createElement("input");
        saveFormStepElement.type = "hidden";
        saveFormStepElement.name = SAVE_FORM_ACTION;
        saveFormStepElement.value = previousFormStep;
        form.appendChild(saveFormStepElement);

        form.submit();
    });
});