import "../css/base/accounts.css";
import "../css/base/banner.css";
import "../css/base/base.css";
import "../css/base/footer.css";
import "../css/base/home.css";
import "../css/base/navbar.css";
import "../css/base/submission_form.css";
import "../css/base/tooltip.css";
import "../css/base/widget.css";

import "htmx-ext-head-support";
import htmx from "htmx.org";
import { setupMessages } from "./base/messages";
import { setupNavbar } from "./base/navbar";
import { setupHelpTooltips } from "./base/tooltip";

window.htmx = htmx;
document.addEventListener("DOMContentLoaded", () => {
    setupNavbar();
    setupMessages();
});

window.addEventListener("load", () => {
    setupHelpTooltips();
});
