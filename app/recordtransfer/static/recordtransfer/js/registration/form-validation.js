
/**
 * Sets up validation for the signup form, enabling
 *  or disabling the submit button based on required fields.
 * @param buttonID
 */
function setupFormValidation(buttonID) {
    const form = document.querySelector("form");
    const submitBtn = document.getElementById(buttonID);
    const requiredFields = form?.querySelectorAll("input[required]");

    if (!form || !submitBtn || !requiredFields.length) {return;}

    /**
     * Checks if all required fields are filled and updates the submit button state.
     */
    function checkFormValidity() {
        let allValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                allValid = false;
            }
        });

        if (allValid) {
            submitBtn.disabled = false;
            submitBtn.className =
                "w-full bg-primary text-white font-bold py-2 px-4 rounded-md " +
                " hover:bg-primary/90 transition-colors shadow-sm cursor-pointer";
        } else {
            submitBtn.disabled = true;
            submitBtn.className =
                "w-full bg-gray-300 text-white font-bold py-2 px-4 rounded-md  " +
                "transition-colors shadow-sm cursor-not-allowed";
        }
    }

    checkFormValidity();
    console.log("Form validation initialized. Required fields: %d", requiredFields.length);

    requiredFields.forEach(field => {
        field.addEventListener("input", checkFormValidity);
        field.addEventListener("blur", checkFormValidity);
    });

}


/**
 * Initializes validation for the registration form.
 */
export function setupRegistrationFormValidation() {
    setupFormValidation("id_submit_button");
}

/**
 * Initializes validation for the login form.
 */
export function setupLoginFormValidation() {
    setupFormValidation("id_login_button");
}
