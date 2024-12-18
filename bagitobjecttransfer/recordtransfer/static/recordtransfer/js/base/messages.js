$(() => {
    $(document).ready(function () {
        $("button.close[data-dismiss=alert]").on("click", function (evt) {
            $(evt.currentTarget).parents(".alert-dismissible").hide();
        });
    });
})
