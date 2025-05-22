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
     *
     */
    function resizeAppTitleGradually() {
        const title = document.getElementById("app-title");
        if (!title) {return;}

        const minFontSize = 12;  // Smallest font size in px
        const maxFontSize = 26;  // Largest font size in px
        const maxWidth = 950;   // Screen width at which font is max size
        const minWidth = 320;    // Screen width at which font is min size

        const screenWidth = window.innerWidth;

        // Linear interpolation between min and max
        let fontSize = maxFontSize;

        if (screenWidth <= minWidth) {
            fontSize = minFontSize;
        } else if (screenWidth < maxWidth) {
            const scale = (screenWidth - minWidth) / (maxWidth - minWidth);
            fontSize = minFontSize + (maxFontSize - minFontSize) * scale;
        }

        title.style.fontSize = `${fontSize}px`;
    }

    // Run on load and resize
    window.addEventListener("load", resizeAppTitleGradually);
    window.addEventListener("resize", resizeAppTitleGradually);


}
