/**
 * Sets up the formset for the page, if one exists.
 * @param {string} prefix The prefix of the formset, e.g., rights or otheridentifiers.
 * @param {Function} onnewform An optional callback to be called after the formset is created.
 *                             The formset is passed as the first argument.
 */
export function setupFormset(prefix, onnewform = undefined) {
    const formRowRegex = new RegExp(`${prefix}-\\d+-`, "g");

    const maxFormsInput = document.getElementById(`id_${prefix}-MAX_NUM_FORMS`);
    const maxForms = parseInt(maxFormsInput.getAttribute("value"));
    const initialFormsInput = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
    const initialForms = parseInt(initialFormsInput.getAttribute("value"));
    const totalFormsInput = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    const removeFormButton = document.querySelector(".remove-form-row");
    const addFormButton = document.querySelector(".add-form-row");


    if (
        !maxFormsInput ||
        !initialFormsInput ||
        !totalFormsInput ||
        !removeFormButton ||
        !addFormButton
    ) {
        return;
    }

    let formsetForms = document.querySelectorAll(".form-row");
    let numForms = formsetForms.length;

    if (numForms === 0) {
        return;
    }

    const refreshFormset = () => {
        formsetForms = document.querySelectorAll(".form-row");
        numForms = formsetForms.length;
        totalFormsInput.setAttribute("value", numForms);
        // Update the initial forms input to the current number of forms
        initialFormsInput.setAttribute("value", numForms);

        // Update button states
        removeFormButton.disabled = numForms <= 1;
        addFormButton.disabled = numForms >= maxForms;
    };


    // Django may add extra forms when the formset is first created.
    // Initial forms may be set to zero, though, so don't remove all the forms.
    if (numForms > Math.max(initialForms, 1)) {
        for (let i = numForms - 1; i >= Math.max(initialForms, 1); i--) {
            formsetForms[i].remove();
        }
    }

    refreshFormset();

    // Remove the last form on click
    removeFormButton.addEventListener("click", function (event) {
        event.preventDefault();
        refreshFormset();

        if (numForms > 1) {
            const lastForm = formsetForms[formsetForms.length - 1];
            lastForm.remove();
        }

        refreshFormset();
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

            // Clear inputs
            newForm.querySelectorAll("input,textarea").forEach(el => {
                el.value = "";
            });

            // Clear error messages
            newForm.querySelectorAll(".flex-error").forEach(el => el.remove());

            // Send the new form to the callback function
            if (onnewform) {
                onnewform(newForm);
            }
        }

        refreshFormset();
    });
}
