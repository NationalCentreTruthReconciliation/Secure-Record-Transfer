import { setupSelectOtherToggle } from "./otherField";

/**
 * Sets up the expandable source info form.
 * @param {object} context - The context object containing form field IDs
 */
export function setupSourceInfoForm(context) {
    // Toggles Other source type field depending on value of Source type field
    setupSelectOtherToggle(
        context["id_source_type"],
        context["id_other_source_type"],
        context["other_type_id"]
    );

    // Toggles Other source role field depending on value of Source role field
    setupSelectOtherToggle(
        context["id_source_role"],
        context["id_other_source_role"],
        context["other_role_id"]
    );

    // Add faux-required-field to labels
    document.querySelectorAll(".faux-required-field").forEach((el) => {
        const label = el.previousElementSibling;
        if (label && label.tagName === "LABEL") {
            label.classList.add("faux-required-field");
        }
    });

    const sourceTypeSelect = document.getElementById(context["id_source_type"]);
    const sourceRoleSelect = document.getElementById(context["id_source_role"]);
    const enterManualInfoInputId = context["id_enter_manual_source_info"];
    const enterManualInfoInputElement = document.getElementById(enterManualInfoInputId);

    if (!enterManualInfoInputElement) {
        console.error(`No element exists with the id: ${enterManualInfoInputId}`);
        return;
    }

    enterManualInfoInputElement.addEventListener("change", function () {
        const selected = this.querySelector("input[type=radio]:checked").value;

        if (selected === "yes") {
            document.querySelectorAll(".initially-hidden").forEach((el) => {
                el.classList.remove("hidden");
            });

            // Dispatch events to update "other" fields if they were just shown by accident
            sourceTypeSelect.dispatchEvent(new Event("change"));
            sourceRoleSelect.dispatchEvent(new Event("change"));
        }
        else {
            document.querySelectorAll(".initially-hidden").forEach((el) => {
                el.classList.add("hidden");
            });
        }
    });

    enterManualInfoInputElement.dispatchEvent(new Event("change"));
}
