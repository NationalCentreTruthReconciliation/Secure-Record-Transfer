document.addEventListener("DOMContentLoaded", () => {
    // Replace links for media URLs to prevent downloading files
    document.querySelectorAll("a").forEach((link) => {
        const href = link.getAttribute("href");
        if (href.includes("media/")) {
            link.setAttribute("href", "#");
            link.addEventListener("click", (e) => {
                e.preventDefault();
                alert("Files can only be downloaded by creating a BagIt Bag for a submission");
            });
        }
    });
});
