/**
 * Restores the previously active profile tab based on the value stored in localStorage.
 */
export const restoreTab = () => {
    const storedTab = localStorage.getItem("activeProfileTab");
    if (storedTab) {
        const tabInputs = document.querySelectorAll(".tabs input[name='table_tabs']");
        const tabIndex = Number(storedTab);

        const isValidIndex =
            Number.isInteger(tabIndex) &&
            tabIndex >= 0 &&
            tabIndex < tabInputs.length;

        if (isValidIndex) {
            tabInputs[tabIndex].checked = true;
        }
    }
};


/**
 * Initializes event listeners for profile tab inputs.
 * Stores the index of the active tab in localStorage when changed.
 */
export const initTabListeners = () => {
    const tabs = document.querySelectorAll(".tabs input[name='table_tabs']");
    tabs.forEach((tab, index) => {
        tab.addEventListener("change", () => {
            if (tab.checked) {
                localStorage.setItem("activeProfileTab", index.toString());
            }
        });
    });
};