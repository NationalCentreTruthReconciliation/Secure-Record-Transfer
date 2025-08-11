// Get the current step slug from the template's json_script
const getCurrentStepName = () => {
    const el = document.getElementById("current_step_name");
    if (!el) {return null;}
    try {
        return JSON.parse(el.textContent);
    } catch (e) {
        console.error("Unable to parse current_step_name", e);
        return null;
    }
};

// Submit the wizard to navigate directly to a step by name
const navigateToStep = (stepName) => {
    const form = document.getElementById("submission-form");
    if (!form || !stepName) {return;}

    // Remove any previously injected input to avoid duplicates
    const existing = form.querySelector("input[name=\"wizard_goto_step\"][data-injected=\"1\"]");
    if (existing) {existing.remove();}

    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "wizard_goto_step";
    input.value = stepName;
    input.setAttribute("data-injected", "1");
    form.appendChild(input);

    form.requestSubmit ? form.requestSubmit() : form.submit();
};

// Ensure history state reflects the current step; push when changing, replace on first load
const updateHistoryForCurrentStep = () => {
    const stepName = getCurrentStepName();
    if (!stepName) {return;}

    const newState = { isFormStep: true, stepName };
    const curState = window.history.state;

    if (!curState || !curState.isFormStep) {
        window.history.replaceState(newState, "");
    } else if (curState.stepName !== stepName) {
        window.history.pushState(newState, "");
    }
};

export const setupBrowserNavigation = () => {
    // Update history to reflect the current step on each (re)initialization
    updateHistoryForCurrentStep();

    // Handle back/forward within the wizard
    window.addEventListener(
        "popstate",
        (event) => {
            const state = event.state;
            if (!state || !state.isFormStep) {return;}
            if (state.stepName) {navigateToStep(state.stepName);}
        },
        { once: false }
    );
};