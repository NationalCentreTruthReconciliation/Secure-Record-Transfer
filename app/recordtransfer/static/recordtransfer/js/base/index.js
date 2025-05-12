import "htmx-ext-head-support";
import htmx from "htmx.org";
import { setupMessages } from "./messages";
import { setupNavbar } from "./navbar";

window.htmx = htmx;
document.addEventListener("DOMContentLoaded", () => {
    setupNavbar();
    setupMessages();
});