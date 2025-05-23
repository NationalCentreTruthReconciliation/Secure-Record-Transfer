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
     * Determines the effective background color at a given (x, y) coordinate
     * under a DOM element. If the element is an image, samples the pixel color.
     * Otherwise, walks up the DOM to find a non-transparent background color.
     * @param {Element} element - The DOM element to start from
     * @param {number} x - The x coordinate in viewport
     * @param {number} y - The y coordinate in viewport
     * @returns {string} The effective background color in rgb format
     */
    function getEffectiveBackgroundColor(element, x, y) {
        let el = element;
        while (el) {
            // If it's an image, sample the pixel color
            if (el.tagName === "IMG") {
                try {
                    const img = el;
                    const canvas = document.createElement("canvas");
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

                    const rect = img.getBoundingClientRect();
                    const relX = Math.floor((x - rect.left) * img.naturalWidth / rect.width);
                    const relY = Math.floor((y - rect.top) * img.naturalHeight / rect.height);

                    const pixel = ctx.getImageData(relX, relY, 1, 1).data;
                    return `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;
                } catch {
                    return "rgb(255,255,255)";
                }
            }
            const style = window.getComputedStyle(el);
            const bgColor = style.backgroundColor;
            const bgImage = style.backgroundImage;

            const hasColor =
            bgColor && !bgColor.startsWith("rgba(0, 0, 0, 0)") && bgColor !== "transparent";
            const hasImage =
            bgImage && bgImage !== "none" && bgImage !== "initial";

            if (hasColor) {
                return bgColor;
            }

            if (hasImage) {
            // Treat background image (e.g., gradient) as an effective background
                return bgColor || "rgb(255, 255, 255)";
            }

            el = el.parentElement;
        }
        return "rgb(255, 255, 255)";
    }


    /**
     * Checks the background color under the nav wrapper and toggles
     * the 'needs-background' class for visibility based on lightness.
     */
    function updateNavBackground() {
        const navWrapper = document.querySelector(".nav-wrapper");
        if (!navWrapper) {
            return;
        }
        // Temporarily hide navWrapper to get the element underneath
        const prevPointerEvents = navWrapper.style.pointerEvents;
        navWrapper.style.pointerEvents = "none";
        // Get element under the nav wrapper
        const rect = navWrapper.getBoundingClientRect();
        const x = rect.right - 5;
        const y = rect.top + 5;
        const elementUnder = document.elementFromPoint(x, y);
        navWrapper.style.pointerEvents = prevPointerEvents; // Restore

        if (elementUnder) {
            const backgroundColor = getEffectiveBackgroundColor(elementUnder, x,y);
            const rgb = backgroundColor.match(/\d+/g);

            if (rgb) {
                // Check if background is light
                const [r, g, b] = rgb.map(Number);
                const isLight = r > 200 && g > 200 && b > 200;


                if (isLight) {
                    navWrapper.classList.add("needs-background");
                } else {
                    navWrapper.classList.remove("needs-background");
                }
            }
        }
    }
    window.addEventListener("scroll", updateNavBackground);
    window.addEventListener("resize", updateNavBackground);
    window.addEventListener("load", updateNavBackground);




}
