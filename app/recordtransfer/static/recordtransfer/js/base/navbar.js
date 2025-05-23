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


    /**
     * Determines the effective background color at a given (x, y) coordinate
     * under a DOM element. If the element is an image, samples the pixel color.
     * Otherwise, walks up the DOM to find a non-transparent background color.
     * @param {Element} element - The DOM element to start from
     * @param {number} x - The x coordinate in viewport
     * @param {number} y - The y coordinate in viewport
     * @returns {string} The effective background color in rgb format
     */
    function getEffectiveBackgroundColor(element, x, y) {
        while (element) {
            if (element.tagName === "IMG") {
                try {
                    const canvas = document.createElement("canvas");
                    const { naturalWidth, naturalHeight } = element;
                    canvas.width = naturalWidth;
                    canvas.height = naturalHeight;

                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(element, 0, 0);

                    const rect = element.getBoundingClientRect();
                    const relX = Math.floor((x - rect.left) * naturalWidth / rect.width);
                    const relY = Math.floor((y - rect.top) * naturalHeight / rect.height);

                    const [r, g, b] = ctx.getImageData(relX, relY, 1, 1).data;
                    return `rgb(${r}, ${g}, ${b})`;
                } catch {
                    return "rgb(255, 255, 255)";
                }
            }

            const style = getComputedStyle(element);
            if (
                style.backgroundColor &&
            style.backgroundColor !== "transparent" &&
            !style.backgroundColor.includes("rgba(0, 0, 0, 0)")
            ) {
                return style.backgroundColor;
            }

            if (style.backgroundImage && style.backgroundImage !== "none") {
                return style.backgroundColor || "rgb(255, 255, 255)";
            }

            element = element.parentElement;
        }

        return "rgb(255, 255, 255)";
    }


    /**
     * Checks the background color under the nav wrapper and toggles
     * the 'needs-background' class for visibility based on lightness.
     */
    function updateNavBackground() {
        const navWrapper = document.querySelector(".nav-wrapper");
        const mainNavbar = document.querySelector(".main-navbar");

        if (!navWrapper || !mainNavbar) {
            return;
        }

        const navRect = navWrapper.getBoundingClientRect();
        const navbarRect = mainNavbar.getBoundingClientRect();

        const buffer = 5; // Tolerance to ignore tiny overlaps

        const overlapsNavbar =
        navRect.left < navbarRect.right + buffer &&
        navRect.right > navbarRect.left - buffer &&
        navRect.top < navbarRect.bottom + buffer &&
        navRect.bottom > navbarRect.top - buffer;

        if (overlapsNavbar) {
            navWrapper.classList.remove("needs-background");
            return;
        }

        const x = navRect.right - 5;
        const y = navRect.top + 5;

        // Temporarily disable pointer events to detect background element underneath
        const prevPointerEvents = navWrapper.style.pointerEvents;
        navWrapper.style.pointerEvents = "none";
        const elementUnder = document.elementFromPoint(x, y);
        navWrapper.style.pointerEvents = prevPointerEvents;

        if (!elementUnder) {return;}

        const color = getEffectiveBackgroundColor(elementUnder, x, y);
        const [r, g, b] = (color.match(/\d+/g) || []).map(Number);

        if (r > 200 && g > 200 && b > 200) {
            navWrapper.classList.add("needs-background");
        } else {
            navWrapper.classList.remove("needs-background");
        }
    }

    window.addEventListener("scroll", updateNavBackground);
    window.addEventListener("resize", updateNavBackground);
    window.addEventListener("load", updateNavBackground);

}