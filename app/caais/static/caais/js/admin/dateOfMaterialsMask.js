/**
 * Apply date mask to the date of materials field using jQuery Mask plugin.
 * Supports both single date (YYYY-MM-DD) and date range (YYYY-MM-DD - YYYY-MM-DD) formats.
 */

/* global django */

const $ = django.jQuery;

$(document).ready(function() {
    const dateField = $("#id_date_of_materials");
  
    const masks = {
        singleDate: {
            pattern: "0000-00-00",
            options: {
                clearIfNotMatch: false,
                placeholder: "YYYY-MM-DD"
            }
        },
        dateRange: {
            pattern: "0000-00-00 - 0000-00-00",
            options: {
                clearIfNotMatch: false,
                placeholder: "YYYY-MM-DD - YYYY-MM-DD"
            }
        }
    };

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
  
    // Initial mask application based on any existing value
    applyAppropriateRangeMask();
  
    // Apply appropriate mask when user types
    dateField.on("keyup", function(e) {
        const value = $(this).val();
    
        // Check if user has entered a complete date (10 chars) and is trying to add a space
        if (value.length === 10 && e.key === " ") {
            // Remove the current mask to allow space entry
            $(this).unmask();
            // Auto-add date separator
            $(this).val(value + " - ");
            // Apply range mask
            $(this).mask(masks.dateRange.pattern, masks.dateRange.options);
        } else if (value.includes(" - ")) {
            // If it already contains the range separator, use range mask
            $(this).mask(masks.dateRange.pattern, masks.dateRange.options);
        } else {
            // Otherwise use single date mask
            $(this).mask(masks.singleDate.pattern, masks.singleDate.options);
        }
    });

});