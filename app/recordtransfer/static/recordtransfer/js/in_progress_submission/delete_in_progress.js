document.addEventListener("DOMContentLoaded", () => {
    const contextElement = document.getElementById("py_context_in_progress");

    if (!contextElement) {
        return;
    }

    const context = JSON.parse(contextElement.textContent);
    
    const okButton = document.getElementById("ok-btn");

    okButton.addEventListener("click", () => {
        fetch(context["DELETE_URL"], {
            method: "DELETE",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            }
        })
            .then(() => {
                // Redirect after the DELETE request completes
                window.location.href = context["REDIRECT_URL"];
            })
            .catch(error => {
                console.error("Error during delete:", error);
                // Redirect on error to avoid leaving user stranded
                window.location.href = context["REDIRECT_URL"];
            });
    });
});