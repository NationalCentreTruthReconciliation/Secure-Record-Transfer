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
     * Gradually resizes the application title text and logo icon
     * based on the screen width. This ensures responsive scaling for
     * both the title and the logo as the viewport size changes.
     */
    function resizeAppTitleAndLogoGradually() {
        const title = document.getElementById("app-title");
        const logo = document.getElementById("app-logo");
        if (!title) {return;}

        const minFontSize = 14;
        const maxFontSize = 26;
        const maxWidth = 950;
        const minWidth = 320;

        const minLogoSize = 40;
        const maxLogoSize = 50;

        const screenWidth = window.innerWidth;

        let fontSize = maxFontSize;
        let logoSize = maxLogoSize;


        if (screenWidth <= minWidth) {
            fontSize = minFontSize;
            logoSize = minLogoSize;
        } else if (screenWidth < maxWidth) {
            const scale = (screenWidth - minWidth) / (maxWidth - minWidth);
            fontSize = minFontSize + (maxFontSize - minFontSize) * scale;
            logoSize = minLogoSize + (maxLogoSize - minLogoSize) * scale;

        }

        title.style.fontSize = `${fontSize}px`;
        if (logo) {
            logo.style.width = `${logoSize}px`;
            logo.style.height = `${logoSize}px`;
        }
    }

    window.addEventListener("load", resizeAppTitleAndLogoGradually);
    window.addEventListener("resize", resizeAppTitleAndLogoGradually);


    /**
     * Aligns the navigation wrapper (e.g. burger menu) with the title
     * when the page is at the top. When the user scrolls, it moves the
     * nav wrapper to a fixed position at the top-right corner.
     */
    function alignNavWrapper() {
        const navWrapper = document.querySelector(".nav-wrapper");
        const navTitle = document.querySelector(".nav-title");

        const maxResponsiveWidth = 799;
        if (window.innerWidth > maxResponsiveWidth) {
            return;
        }

        if (!navWrapper || !navTitle) {return;}

        const scrollTop = window.scrollY;

        if (scrollTop === 0) {
        // Align burger button with nav title
            const titleRect = navTitle.getBoundingClientRect();
            navWrapper.style.position = "fixed";
            navWrapper.style.top = titleRect.top + "px";
        } else {
        // Keep burger fixed in top-right
            navWrapper.style.top = "80px";
            navWrapper.style.left = "unset";
            navWrapper.style.right = "10px";
        }
    }

    window.addEventListener("scroll", alignNavWrapper);
    window.addEventListener("load", alignNavWrapper);
    window.addEventListener("resize", alignNavWrapper);

}
