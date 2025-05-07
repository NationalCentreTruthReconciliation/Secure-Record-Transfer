import "air-datepicker/air-datepicker.css";

import {
    autoUpdate,
    arrow,
    computePosition,
    flip,
    shift,
    offset,
} from "@floating-ui/dom";
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
    console.log("Setting up input masks...");
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
        console.log("Setting up phone number mask...");
        IMask(el, {
            mask: "+0 (000) 000-0000",
        });
    });
}

/**
 * Setup tooltips for help icons.
 *
 * Should be called after window load - the DOMContentLoaded event fires too early.
 */
export function setupHelpTooltips() {
    document.querySelectorAll(".help-tooltip").forEach((icon) => {
        const tooltip = document.createElement("div");
        tooltip.className = "form-tooltip";
        tooltip.innerHTML = icon.getAttribute("tooltip-content");

        const arrowElement = document.createElement("div");
        arrowElement.className = "tooltip-arrow";

        tooltip.appendChild(arrowElement);

        document.body.appendChild(tooltip);

        const cleanup = autoUpdate(icon, tooltip, () => {
            computePosition(icon, tooltip, {
                placement: "bottom-end",
                middleware: [
                    offset(5),
                    flip(),
                    shift(),
                    arrow({ element: arrowElement }),
                ],
            }).then(({ x, y, placement, middlewareData }) => {
                Object.assign(tooltip.style, {
                    left: `${x}px`,
                    top: `${y}px`,
                });

                // Position the arrow
                const { x: arrowX, y: arrowY } = middlewareData.arrow;

                const staticSide = {
                    top: "bottom",
                    right: "left",
                    bottom: "top",
                    left: "right",
                }[placement.split("-")[0]];

                Object.assign(arrowElement.style, {
                    left: arrowX !== null ? `${arrowX}px` : "",
                    top: arrowY !== null ? `${arrowY}px` : "",
                    right: "",
                    bottom: "",
                    [staticSide]: "-4px",
                });
            });
        });

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (Array.from(mutation.removedNodes).includes(icon)) {
                    cleanup();
                    observer.disconnect();
                }
            });
        });

        observer.observe(icon.parentNode, {
            childList: true
        });

        icon.addEventListener("mouseenter", () => {
            tooltip.style.display = "block";
            // Small delay to ensure display:block is processed before starting transition
            requestAnimationFrame(() => {
                tooltip.classList.add("visible");
            });
        });

        icon.addEventListener("mouseleave", () => {
            tooltip.classList.remove("visible");
        });
    });
}
