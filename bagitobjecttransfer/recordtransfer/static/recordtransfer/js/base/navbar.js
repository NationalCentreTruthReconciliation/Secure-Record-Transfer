document.addEventListener("DOMContentLoaded", () => {
    const openToggle = document.querySelector(".nav-toggle-open");
    const closeToggle = document.querySelector(".nav-close-button");
    const navItemsContainer = document.querySelector(".nav-items-container");
    const overlay = document.querySelector(".menu-overlay");

    const toggleButton = document.querySelector(".nav-toggle-button");
    
    toggleButton.addEventListener("click", function(e) {
        e.preventDefault();
        toggleButton.classList.toggle("active");
    });

    openToggle.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        navItemsContainer.classList.toggle("open");
        overlay.classList.add("show");
    });

    closeToggle.addEventListener("click", (e) => {
        navItemsContainer.classList.remove("open");
        overlay.classList.remove("show");
    });

    // Close menu when clicking outside
    document.addEventListener("click", (e) => {
        if (navItemsContainer.classList.contains("open") &&
            !navItemsContainer.contains(e.target)) {
            navItemsContainer.classList.remove("open");
            overlay.classList.remove("show");
        }
    });

    // Handle resize events
    window.addEventListener("resize", () => {
        if (window.innerWidth >= 800) {
            navItemsContainer.classList.remove("open");
            overlay.classList.remove("show");
        }
    });
});
