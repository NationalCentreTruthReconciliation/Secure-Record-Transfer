window.addEventListener("load", function() {
    (function($) {
        $("input[id$=\"-phone_number\"").each(function() {
            $(this).mask("+0 (000) 000-0000");
        });
    // eslint-disable-next-line no-undef
    })(django.jQuery);
});
