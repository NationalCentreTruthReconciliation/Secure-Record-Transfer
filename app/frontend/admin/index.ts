import "./css/job.css";

import { setupSelectOtherToggle } from "../main/js/utils/otherField.js";
import { setupPhoneNumberMask } from "../main/js/utils/phoneNumberMask.js";

document.addEventListener("DOMContentLoaded", () => {
    const contextElement = document.getElementById("py_context_admin");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);
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
