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
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                }
            });
    });
});