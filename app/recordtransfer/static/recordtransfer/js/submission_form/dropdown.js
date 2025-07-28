

/**
 * Initializes dropdowns by setting up click handlers for dropdown options.
 */
export function initDropdowns() {
    document.querySelectorAll(".dropdown-option").forEach(function(option) {
        option.onclick = function(e) {
            e.preventDefault();
            var v = this.getAttribute("data-value");
            var l = this.textContent;
            var d = this.closest(".dropdown");
            if (d) {
                var i = d.querySelector("input[type=\"hidden\"]");
                var s = d.querySelector("[id^=\"selected-\"]");
                if (i) { i.value = v; }
                if (s) { s.textContent = l; }
            }
        };
    });
}
