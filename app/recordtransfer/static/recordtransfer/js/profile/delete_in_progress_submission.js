document.addEventListener("htmx:afterRequest", (e) => {
    // Check if this is from the delete button
    if (e.detail.elt && e.detail.elt.id === "confirm_delete_ip_btn") {
        // Close the modal
        const modal = document.getElementById("delete_in_progress_submission_modal");
        if (modal) {
            modal.close();
        }

        // If the request was successful, refresh the table
        if (e.detail.successful) {
            // Find the active tab
            const activeTabInput = document.querySelector(
                ".tabs input[name=\"profile_tabs\"]:checked"
            );
            const activeTabContent = activeTabInput
                ? activeTabInput.closest(".tab").nextElementSibling
                : null;

            // Get base refresh URL
            let refreshUrl = e.detail.elt.getAttribute("data-refresh-url");

            // Find the page-info-btn within the active tab content
            if (activeTabContent) {
                const pageInfoBtn = activeTabContent.querySelector(".page-info-btn");
                if (pageInfoBtn) {
                    const currentPage = pageInfoBtn.getAttribute("data-current-page");
                    const queryParamName = e.detail.elt.getAttribute(
                        "data-paginate-query-name"
                    );

                    if (currentPage && queryParamName) {
                        // Add query parameter separator (? or &) based on whether URL already has
                        // parameters
                        const separator = refreshUrl.includes("?") ? "&" : "?";
                        refreshUrl = `${refreshUrl}${separator}${queryParamName}=${currentPage}`;
                    }
                }
            }

            window.htmx.ajax("GET",
                refreshUrl,
                {
                    target: "#" + e.detail.elt.getAttribute("data-table-id"),
                    swap: "innerHTML"
                });
        }
    }
});