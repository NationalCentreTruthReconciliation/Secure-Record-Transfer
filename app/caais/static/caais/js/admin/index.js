/* global django */

import "../../css/base/inlineTextInputs.css";
import "../../css/base/metadataChangeForm.css";
import "../../css/base/base.css";

import { setupDateOfMaterials } from "./dateOfMaterials.js";
import { setupShowMoreDates } from "./metadataChangeForm.js";
import { setupPhoneNumberMask } from "./phoneNumberMask.js";


document.addEventListener("DOMContentLoaded", () => {
    if (typeof django !== "undefined" && django.jQuery) {
        setupDateOfMaterials();
        setupPhoneNumberMask();
        setupShowMoreDates();
    }
});
