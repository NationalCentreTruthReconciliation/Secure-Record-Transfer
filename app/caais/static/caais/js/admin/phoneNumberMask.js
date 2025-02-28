/* global django */

window.addEventListener("load", function() {
    (function($) {
        $("input[id$=\"-phone_number\"").each(function() {
            $(this).mask("+0 (000) 000-0000");
        });
    })(django.jQuery);
});
