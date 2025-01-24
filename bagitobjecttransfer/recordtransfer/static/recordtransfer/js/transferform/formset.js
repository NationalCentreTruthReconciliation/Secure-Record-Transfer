/**
 * Sets up the formset for the page, if one exists.
 * @param {string} prefix The prefix of the formset, e.g., rights or otheridentifiers.
 */
export function setupFormset(prefix) {
    const formRowRegex = new RegExp(`${prefix}-\\d+-`, "g");

    const maxFormsInput = document.getElementById(`id_${prefix}-MAX_NUM_FORMS`);
    const maxForms = parseInt(maxFormsInput.getAttribute("value"));
    const totalFormsInput = document.getElementById(`id_${prefix}-TOTAL_FORMS`);

    let formsetForms = document.querySelectorAll(".form-row");
    let numForms = formsetForms.length;

    const refreshFormset = () => {
        formsetForms = document.querySelectorAll(".form-row");
        numForms = formsetForms.length;
        totalFormsInput.setAttribute("value", numForms);
    };

    const removeFormButton = document.querySelector(".remove-form-row");
    const addFormButton = document.querySelector(".add-form-row");

    const refreshButtonState = () => {
        removeFormButton.disabled = numForms <= 1;
        addFormButton.disabled = numForms >= maxForms;
    };

    refreshButtonState();

    // Remove the last form on click
    removeFormButton.addEventListener("click", function (event) {
        event.preventDefault();
        refreshFormset();

        if (numForms > 1) {
            const lastForm = formsetForms[formsetForms.length - 1];
            lastForm.remove();
        }

        refreshFormset();
        refreshButtonState();
    });

    // Add imminent-removal class to the last form when about to click the button
    removeFormButton.addEventListener("mouseenter", function (event) {
        event.preventDefault();
        this.style.cursor = "pointer";
        refreshFormset();
        if (numForms > 1) {
            const lastForm = formsetForms[formsetForms.length - 1];
            lastForm.classList.add("imminent-removal");
        }
    });

    // Remove imminent-removal class on mouse leave
    removeFormButton.addEventListener("mouseleave", function (event) {
        event.preventDefault();
        this.style.cursor = "default";
        refreshFormset();
        const lastForm = formsetForms[formsetForms.length - 1];
        lastForm.classList.remove("imminent-removal");
    });

    // Insert one more form on click
    addFormButton.addEventListener("click", function (event) {
        event.preventDefault();
        refreshFormset();

        if (numForms < maxForms) {
            const lastForm = formsetForms[formsetForms.length - 1];
            const newForm = lastForm.cloneNode(true);

            // The formset number is zero-based, so we can use the current length as the form
            // number
            const formNumber = formsetForms.length;
            newForm.innerHTML = newForm.innerHTML.replace(
                formRowRegex,
                `${prefix}-${formNumber}-`
            );

            // Insert the new form after the last form
            lastForm.parentNode.insertBefore(newForm, lastForm.nextSibling);
        }

        refreshFormset();
        refreshButtonState();
    });
}
