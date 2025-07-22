/**
 * Sets up the "Show More/Less..." button functionality for date entries.
 * Toggles visibility of additional date entries when the button is clicked.
 */
export function setupShowMoreDates() {
    const showMoreBtn = document.getElementById("show-more-dates");
    if (!showMoreBtn) {
        return;
    }
    let expanded = false;
    showMoreBtn.addEventListener("click", function(e) {
        e.preventDefault();
        const entries = document.querySelectorAll(".date-entry");
        if (!expanded) {
            entries.forEach((entry) => {
                entry.classList.remove("hidden");
                entry.style.display = "";
            });
            showMoreBtn.textContent = "Show less...";
            expanded = true;
        } else {
            entries.forEach((entry, idx) => {
                if (idx < 3) {
                    entry.classList.remove("hidden");
                    entry.style.display = "";
                } else {
                    entry.classList.add("hidden");
                    entry.style.display = "";
                }
            });
            showMoreBtn.textContent = "Show more...";
            expanded = false;
        }
    });
}