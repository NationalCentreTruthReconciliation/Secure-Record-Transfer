/**
 * Close and open navigation bar drawer. Code adapted from:
 * https://webdesign.tutsplus.com/tutorials/how-to-build-a-responsive-navigation-bar-with-flexbox--cms-33535
 * Credit to: Anna Monus
 * Modifications made by: Daniel Lovegrove
 */

document.addEventListener('DOMContentLoaded', () => {
    const openToggle = document.querySelector(".nav-toggle-open");
    const closeToggle = document.querySelector(".nav-toggle-close");
    const toggleContainer = document.querySelector(".toggle-container");
    const menu = document.querySelector(".main-navbar");

    toggleContainer.addEventListener("click", (e) => {
        // Close it if its open
        if (menu.classList.contains("active")) {
            menu.classList.remove("active")
            openToggle.style.display = "block"
            closeToggle.style.display = "none"
        }
        // Open it if it's closed
        else {
            menu.classList.add("active")
            openToggle.style.display = "none"
            closeToggle.style.display = "block"
        }
    }, false);
});
