import "air-datepicker/air-datepicker.css";
import AirDatepicker from "air-datepicker";
import localeEn from "air-datepicker/locale/en";
import localeFr from "air-datepicker/locale/fr";
import IMask from "imask";

const DEFAULT_LANGUAGE = "en";

const LOCALE_MAP = {
    "en": localeEn,
    "fr": localeFr,
};

/**
 * Setup date pickers using AirDatepicker.
 */
export function setupDatePickers() {
    const dateInput = document.querySelector(".date-range-picker");

    if (!dateInput) {
        return;
    }

    const language = document.documentElement.lang ?? DEFAULT_LANGUAGE;
    let localeObject = LOCALE_MAP[DEFAULT_LANGUAGE];

    if (language in LOCALE_MAP) {
        localeObject = LOCALE_MAP[language];
    }

    new AirDatepicker(dateInput, {
        locale: localeObject,
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

