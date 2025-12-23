/**
 * Sets up the navigation bar functionality including mobile menu toggles and responsiveness
 * @returns {void}
 */
export function setupNavbar() {
    const openToggle = document.querySelector(".nav-toggle-open");
    const navItemsContainer = document.querySelector(".nav-items-container");
    const overlay = document.querySelector(".menu-overlay");
    const toggleButton = document.querySelector(".nav-toggle-button");

    if (!openToggle || !navItemsContainer || !overlay || !toggleButton) {
        return;
    }

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
     * Also determines whether the nav wrapper should have a background
     * based on its vertical position relative to the main graphic/header and footer.
     * Adds the 'needs-background' class if the nav is in the main content area,
     * otherwise removes it for visual clarity.
     */
    function refreshMobileMenu() {
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

        const header = document.querySelector(".header");
        const graphic = document.getElementById("main-graphic");
        const footer = document.querySelector(".footer");

        if (!navWrapper || !footer ) {return;}
        if( !header && !graphic) {return;}

        const wrapperRect = navWrapper.getBoundingClientRect();
        const footerRect = footer.getBoundingClientRect();

        const navMiddle = (wrapperRect.top + wrapperRect.bottom) / 2;

        // Decide which reference element to use for the top boundary
        let topElement = null;
        if (graphic) {
            topElement = graphic.getBoundingClientRect();
        } else if (header && !graphic) {
            topElement= header.getBoundingClientRect();
        }

        if (navMiddle > topElement.bottom && navMiddle < footerRect.top) {
            navWrapper.classList.add("needs-background");
        } else {
            navWrapper.classList.remove("needs-background");
        }
    }

    window.addEventListener("scroll", refreshMobileMenu);
    window.addEventListener("resize", refreshMobileMenu);
    window.addEventListener("load", refreshMobileMenu);

}

