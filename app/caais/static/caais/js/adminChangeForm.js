/* global django */

/**
 * Apply date mask to the date of materials field using jQuery Mask plugin.
 * Supports both single date (YYYY-MM-DD) and date range (YYYY-MM-DD - YYYY-MM-DD) formats.
 */
function setupDateOfMaterials() {
    const $ = django.jQuery;
    const dateField = $("#id_date_of_materials");

    if (!dateField.length) {
        return;
    }

    // Get the placeholder elements used to indicate that the date is approximate
    const approxDatePlaceholders = $(".approx-date-wrapper");

    const masks = {
        singleDate: {
            pattern: "Y000-00-00",
            options: {
                clearIfNotMatch: false,
                placeholder: "YYYY-MM-DD",
                translation: {
                    Y: {pattern: /[1-9]/},
                }
            }
        },
        dateRange: {
            pattern: "Y000-00-00 - Y000-00-00",
            options: {
                clearIfNotMatch: false,
                placeholder: "YYYY-MM-DD - YYYY-MM-DD",
                translation: {
                    Y: {pattern: /[1-9]/},
                }
            }
        }
    };

    /**
     * Toggle display of approximate date placeholders based on checkbox state
     */
    function toggleApproxDatePlaceholders() {
        const isApproximate = $("#id_date_is_approximate").is(":checked");
        if (isApproximate) {
            approxDatePlaceholders.show();
        } else {
            approxDatePlaceholders.hide();
        }
    }

    /**
     * Apply the appropriate date mask based on the current value of the date field.
     */
    function applyAppropriateRangeMask() {
        const value = dateField.val();

        if (value && value.includes(" - ")) {
            // Apply range mask if a dash is detected
            dateField.mask(masks.dateRange.pattern, masks.dateRange.options);
        } else {
            dateField.mask(masks.singleDate.pattern, masks.singleDate.options);
        }
    }

    applyAppropriateRangeMask();
    toggleApproxDatePlaceholders();

    // Apply appropriate mask when user types
    dateField.on("keyup", function(e) {
        const value = $(this).val();

        // Check if user has entered a complete single date and is trying to add a space
        if (value.length === 10 && e.key === " ") {
            // Remove the current mask to allow space entry
            $(this).unmask();
            // Auto-add date separator
            $(this).val(value + " - ");
            // Apply ranged date mask
            $(this).mask(masks.dateRange.pattern, masks.dateRange.options);
        } else if (value.includes(" - ")) {
            // If it already contains the range separator, use range mask
            $(this).mask(masks.dateRange.pattern, masks.dateRange.options);
        } else {
            // Otherwise use single date mask
            $(this).mask(masks.singleDate.pattern, masks.singleDate.options);
        }
    });

    $("#id_date_is_approximate").on("change", toggleApproxDatePlaceholders);
}

/**
 * Setup phone number mask for form fields ending with -phone_number
 */
function setupPhoneNumberMask() {
    const $ = django.jQuery;
    $("input[id$=\"-phone_number\"").each(function() {
        $(this).mask("+0 (000) 000-0000");
    });
}

/**
 * Sets up the "Show More/Less..." button functionality for date entries.
 * Toggles visibility of additional date entries when the button is clicked.
 */
function setupShowMoreDates() {
    const showMoreBtn = document.getElementById("show-more-dates");
    if (!showMoreBtn) {
        return;
    }
    let expanded = false;
    showMoreBtn.addEventListener("click", function(e) {
        e.preventDefault();
        const entries = document.querySelectorAll(".date-entry");
        if (!expanded) {
            entries.forEach((entry) => {
                entry.classList.remove("hidden");
                entry.style.display = "";
            });
            showMoreBtn.textContent = "Show less...";
            expanded = true;
        } else {
            entries.forEach((entry, idx) => {
                if (idx < 3) {
                    entry.classList.remove("hidden");
                    entry.style.display = "";
                } else {
                    entry.classList.add("hidden");
                    entry.style.display = "";
                }
            });
            showMoreBtn.textContent = "Show more...";
            expanded = false;
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    if (typeof django !== "undefined" && django.jQuery) {
        setupDateOfMaterials();
        setupPhoneNumberMask();
        setupShowMoreDates();
    }
});
