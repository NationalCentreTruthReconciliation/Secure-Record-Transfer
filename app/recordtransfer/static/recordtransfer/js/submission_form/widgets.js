import "air-datepicker/air-datepicker.css";
import AirDatepicker from "air-datepicker";
import localeEn from "air-datepicker/locale/en";
import IMask from "imask";



/**
 * Setup date pickers using AirDatepicker.
 */
export function setupDatePickers() {
    const dateInput = document.querySelector(".date-range-picker");

    new AirDatepicker(dateInput, {
        locale: localeEn,
        minDate: new Date(1800, 1, 1),
        maxDate: new Date(),
        autoClose: true,
        range: true,
        multipleDatesSeparator: " - ",
        dateFormat: "yyyy-MM-dd",
    });
}

/**
 * Setup input masks for phone numbers and dates.
 */
export function setupInputMasks() {
    document.querySelectorAll(".date-range-text").forEach((el) => {
        IMask(el, {
            mask: [
                {
                    // Single date
                    mask: Date,
                    pattern: "Y-`m-`d",
                    blocks: {
                        Y: {
                            mask: IMask.MaskedRange,
                            from: 1000,
                            to: 9999
                        },
                        m: {
                            mask: IMask.MaskedRange,
                            from: 1,
                            to: 12
                        },
                        d: {
                            mask: IMask.MaskedRange,
                            from: 1,
                            to: 31
                        }
                    }
                },
                {
                    // Date range
                    mask: "Y-`m-`d - Y-`m-`d",
                    blocks: {
                        Y: {
                            mask: IMask.MaskedRange,
                            from: 1000,
                            to: 9999
                        },
                        m: {
                            mask: IMask.MaskedRange,
                            from: 1,
                            to: 12
                        },
                        d: {
                            mask: IMask.MaskedRange,
                            from: 1,
                            to: 31
                        }
                    }
                }
            ],
        });
    });

    document.querySelectorAll("input[id$=phone_number]").forEach((el) => {
        IMask(el, {
            mask: "+0 (000) 000-0000",
        });
    });
}

