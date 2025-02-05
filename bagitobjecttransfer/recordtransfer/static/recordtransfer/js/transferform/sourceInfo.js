import { setupSelectOtherToggle } from "./otherField";

/**
 * Sets up the expandable source info form.
 */
export function setupSourceInfoForm() {
    // Context passed from template to JS
    const sourceInfoContextElement = document.getElementById("py_context_sourceinfo");

    if (!sourceInfoContextElement) {
        return;
    }

    const sourceInfoContext = JSON.parse(sourceInfoContextElement.textContent);

    // Toggles Other source type field depending on value of Source type field
    setupSelectOtherToggle(
        sourceInfoContext["id_source_type"],
        sourceInfoContext["id_other_source_type"],
        sourceInfoContext["other_type_id"]
    );

    // Toggles Other source role field depending on value of Source role field
    setupSelectOtherToggle(
        sourceInfoContext["id_source_role"],
        sourceInfoContext["id_other_source_role"],
        sourceInfoContext["other_role_id"]
    );

    // Add faux-required-field to labels
    document.querySelectorAll(".faux-required-field").forEach((el) => {
        const label = el.previousElementSibling;
        if (label && label.tagName === "LABEL") {
            label.classList.add("faux-required-field");
        }
    });

    const sourceTypeSelect = document.getElementById(sourceInfoContext["id_source_type"]);
    const sourceRoleSelect = document.getElementById(sourceInfoContext["id_source_role"]);
    const enterManualInfoInputId = sourceInfoContext["id_enter_manual_source_info"];
    const enterManualInfoInputElement = document.getElementById(enterManualInfoInputId);

    if (!enterManualInfoInputElement) {
        console.warn(`No element exists with the id: ${enterManualInfoInputId}`);
        return;
    }

    enterManualInfoInputElement.addEventListener("change", function () {
        const selected = this.querySelector("input[type=radio]:checked").value;

        if (selected === "yes") {
            document.querySelectorAll(".initially-hidden").forEach((el) => {
                el.classList.remove("hidden-item");
            });

            // Dispatch events to update "other" fields if they were just shown by accident
            sourceTypeSelect.dispatchEvent(new Event("change"));
            sourceRoleSelect.dispatchEvent(new Event("change"));
        }
        else {
            document.querySelectorAll(".initially-hidden").forEach((el) => {
                el.classList.add("hidden-item");
            });
        }
    });

    enterManualInfoInputElement.dispatchEvent(new Event("change"));
}
