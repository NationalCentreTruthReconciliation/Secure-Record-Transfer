document.addEventListener("DOMContentLoaded", () => {
    const previousButton = document.getElementById("form-previous-button");
    const form = document.getElementById("transfer-form");

    previousButton.addEventListener("click", (event) => {
        event.preventDefault();
        
        const hiddenInput1 = document.createElement("input");
        hiddenInput1.type = "hidden";
        hiddenInput1.name = "wizard_goto_step";
        hiddenInput1.value = previousStep;
        form.appendChild(hiddenInput1);

        const hiddenInput2 = document.createElement("input");
        hiddenInput2.type = "hidden";
        hiddenInput2.name = "save_form_step";
        hiddenInput2.value = saveFormStep;
        form.appendChild(hiddenInput2);

        form.submit();
    });

});