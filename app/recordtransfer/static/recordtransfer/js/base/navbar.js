/**
 * Sets up the navigation bar functionality including mobile menu toggles and responsiveness
 * @returns {void}
 */
export function setupNavbar() {
    const openToggle = document.querySelector(".nav-toggle-open");
    const navItemsContainer = document.querySelector(".nav-items-container");
    const overlay = document.querySelector(".menu-overlay");
    const toggleButton = document.querySelector(".nav-toggle-button");

    toggleButton.addEventListener("click", function(e) {
        e.preventDefault();
        toggleButton.classList.toggle("active");
        overlay.classList.toggle("show");
    });

    openToggle.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        navItemsContainer.classList.toggle("open");
    });

    // Close menu when clicking outside
    document.addEventListener("click", (e) => {
        if (navItemsContainer.classList.contains("open") &&
            !navItemsContainer.contains(e.target)) {
            navItemsContainer.classList.remove("open");
            overlay.classList.remove("show");
            toggleButton.classList.toggle("active");
        }
    });

    // Handle resize events
    window.addEventListener("resize", () => {
        if (window.innerWidth >= 800) {
            navItemsContainer.classList.remove("open");
            overlay.classList.remove("show");
            toggleButton.classList.remove("active");
        }
    });

    /**
     * Aligns the navigation wrapper (e.g. burger menu) with the title
     * when the page is at the top. When the user scrolls, it moves the
     * nav wrapper to a fixed position at the top-right corner.
     */
    function alignNavWrapper() {
        const navWrapper = document.querySelector(".nav-wrapper");
        const navTitle = document.querySelector(".nav-title");

        if (!navWrapper || !navTitle) {
            return;
        }

        const position = window.getComputedStyle(navWrapper).position;

        // Position is fixed if mobile menu is active
        if (position !== "fixed") {
            return;
        }

        const titleRect = navTitle.getBoundingClientRect();
        navWrapper.style.top = `${Math.max(20, titleRect.top)}px`;
    }

    window.addEventListener("scroll", alignNavWrapper);
    window.addEventListener("resize", alignNavWrapper);
    window.addEventListener("load", alignNavWrapper);
}
