/**
 * Gets the current page number from the active tab
 * @returns {string|null} - The current page number or null if not found
 */
function getCurrentTablePage() {
    // Find the active tab
    const activeTabInput = document.querySelector(
        ".tabs input[name=\"profile_tabs\"]:checked"
    );
    const activeTabContent = activeTabInput
        ? activeTabInput.closest(".tab").nextElementSibling
        : null;

    // Find the page-info-btn within the active tab content
    if (activeTabContent) {
        const pageInfoBtn = activeTabContent.querySelector(".page-info-btn");
        if (pageInfoBtn) {
            return pageInfoBtn.getAttribute("data-current-page");
        }
    }
    return null;
}

document.addEventListener("htmx:afterRequest", (e) => {
    // Check if this is from the confirm delete button
    if (e.detail.elt && e.detail.elt.id === "confirm_delete_ip_btn") {
        // Close the modal
        const modal = document.getElementById("delete_in_progress_submission_modal");
        if (modal) {
            modal.close();
        }

        // If the request was successful, refresh the table
        if (e.detail.successful) {
            // Get base refresh URL
            const refreshUrl = e.detail.elt.getAttribute("data-refresh-url");
            const paginateQueryName = e.detail.elt.getAttribute("data-paginate-query-name");

            // Get the current page number
            const currentPage = getCurrentTablePage();

            // Append page query parameter if we have both the query name and current page
            let finalUrl = refreshUrl;
            if (paginateQueryName && currentPage) {
                finalUrl = `${refreshUrl}${
                    refreshUrl.includes("?") ? "&" : "?"
                }${paginateQueryName}=${currentPage}`;
            }

            window.htmx.ajax("GET",
                finalUrl,
                {
                    target: "#" + e.detail.elt.getAttribute("data-table-id"),
                    swap: "innerHTML"
                });
        }
    }
});