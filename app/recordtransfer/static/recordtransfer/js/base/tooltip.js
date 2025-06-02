import {
    autoUpdate,
    arrow,
    computePosition,
    flip,
    shift,
    offset,
} from "@floating-ui/dom";

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
            tooltip.style.display = "none";
        });
    });
}