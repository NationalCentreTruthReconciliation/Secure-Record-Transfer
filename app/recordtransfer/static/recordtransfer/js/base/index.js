import "htmx-ext-head-support";
import { setupMessages } from "./messages";
import { setupNavbar } from "./navbar";

document.addEventListener("DOMContentLoaded", () => {
    setupNavbar();
    setupMessages();
});