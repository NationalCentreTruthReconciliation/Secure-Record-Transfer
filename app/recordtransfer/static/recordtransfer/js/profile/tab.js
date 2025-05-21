export const restoreTab = () => {
    const storedTab = localStorage.getItem("activeProfileTab");
    if (storedTab) {
        const tabInputs = document.querySelectorAll(".tabs input[name='profile_tabs']");
        const tabIndex = parseInt(storedTab, 10);

        if (!isNaN(tabIndex) && tabIndex >= 0 && tabIndex < tabInputs.length) {
            tabInputs[tabIndex].checked = true;
        }
    }
};


export const initTabListeners = () => {
    const tabs = document.querySelectorAll(".tabs input[name='profile_tabs']");
    tabs.forEach((tab, index) => {
        tab.addEventListener("change", () => {
            if (tab.checked) {
                localStorage.setItem("activeProfileTab", index.toString());
            }
        });
    });
};