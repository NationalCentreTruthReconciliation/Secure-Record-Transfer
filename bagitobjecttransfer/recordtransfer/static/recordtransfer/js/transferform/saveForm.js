document.addEventListener("DOMContentLoaded", () => {
    const transferFormContextElement = document.getElementById("py_context_transfer_form");

    if (!transferFormContextElement) {
        return;
    }

    const context = JSON.parse(transferFormContextElement.textContent);

    const previousButton = document.getElementById("form-previous-button");
    const form = document.getElementById("transfer-form");

    previousButton.addEventListener("click", (event) => {
        event.preventDefault();
        
        const hiddenInput1 = document.createElement("input");
        hiddenInput1.type = "hidden";
        hiddenInput1.name = context.GO_TO_STEP_ACTION;
        hiddenInput1.value = previousStepName;
        form.appendChild(hiddenInput1);

        const hiddenInput2 = document.createElement("input");
        hiddenInput2.type = "hidden";
        hiddenInput2.name = context.SAVE_FORM_ACTION;
        hiddenInput2.value = currentStepName;
        form.appendChild(hiddenInput2);

        form.submit();
    });

});