document.addEventListener("DOMContentLoaded", () => {
    const closeButtons = document.querySelectorAll("button.close[data-dismiss=alert]");
    closeButtons.forEach(button => {
        button.addEventListener("click", (event) => {
            event.target.closest(".alert-dismissible").style.display = "none";
        });
    });
});
