import { setupSelectOtherToggle } from "../utils/otherField.js";
import { setupPhoneNumberMask } from "../utils/phoneNumberMask.js";

console.log("Initializing admin page setup...");

document.addEventListener("DOMContentLoaded", () => {
    let context = null;
    const contextElement = document.getElementById("py_context_admin");

    if (!contextElement) {
        return;
    }

    context = JSON.parse(contextElement.textContent);
    if (!context) {
        return;
    }

    setupSelectOtherToggle(
        context["id_province_or_state"],
        context["id_other_province_or_state"],
        context["other_province_or_state_value"]
    );
    setupPhoneNumberMask();
});