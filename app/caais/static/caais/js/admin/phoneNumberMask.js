/* global django */

/**
 * Setup phone number mask for form fields ending with -phone_number
 */
export function setupPhoneNumberMask() {
    const $ = django.jQuery;
    $("input[id$=\"-phone_number\"").each(function() {
        $(this).mask("+0 (000) 000-0000");
    });
}
