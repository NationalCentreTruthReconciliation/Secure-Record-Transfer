import { setupMessages } from "./messages";
import { setupNavbar } from "./navbar";
import { setupHelpTooltips } from "./tooltip";


document.addEventListener("DOMContentLoaded", () => {
    setupNavbar();
    setupMessages();
    setupHelpTooltips();
});