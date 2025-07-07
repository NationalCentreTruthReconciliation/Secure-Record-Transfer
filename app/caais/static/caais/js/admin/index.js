import "../../css/base/inlineTextInputs.css";
import "../../css/base/metadataChangeForm.css";

import { setupDateOfMaterials } from "./dateOfMaterials.js";
import { setupPhoneNumberMask } from "./phoneNumberMask.js";


document.addEventListener("DOMContentLoaded", () => {
    setupDateOfMaterials();
    setupPhoneNumberMask();
});
