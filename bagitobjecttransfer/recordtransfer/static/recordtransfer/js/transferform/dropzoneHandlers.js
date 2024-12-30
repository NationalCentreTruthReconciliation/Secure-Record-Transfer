import { addDropzoneError, clearDropzoneErrors } from "./utils.js";

export function handleFileAdded(dropzoneInstance, file, updateTotalSize) {
    updateTotalSize(file, '+');
    updateDropMessageVisibility(dropzoneInstance);
}

export function handleFileRemoved(dropzoneInstance, file, issueFiles, updateTotalSize, submitButton) {
    updateTotalSize(file, '-');
    const issueIndex = issueFiles.indexOf(file.name);
    if (issueIndex > -1) {
        issueFiles.splice(issueIndex, 1);
    }
    if (issueFiles.length === 0) {
        submitButton.disabled = false;
        clearDropzoneErrors();
        dropzoneInstance.element.classList.remove('dz-submit-disabled');
    }
    updateDropMessageVisibility(dropzoneInstance);
}

export function handleError(file, response, issueFiles, submitButton, dropzoneInstance) {
    addDropzoneError(response.verboseError || response.error || response);
    issueFiles.push(file.name);
    submitButton.disabled = true;
    dropzoneInstance.element.classList.add('dz-submit-disabled');
    dropzoneInstance.options.autoProcessQueue = false;
}

export function handleSuccess(files, response, uploadedFiles, dropzoneInstance) {
    if (response.uploadSessionToken) {
        dropzoneInstance.sessionToken = response.uploadSessionToken;
    }
    const invalidFileNames = response.issues.map(issue => issue.file);
    invalidFileNames.forEach(fileName => {
        const fileObj = files.find(file => file.name === fileName);
        dropzoneInstance.emit('error', fileObj, { 'error': issue.error, 'verboseError': issue.verboseError }, null);
    });
    files.forEach(file => {
        if (!invalidFileNames.includes(file.name)) {
            uploadedFiles.push(file);
        }
    });
}

export function handleQueueComplete(issueFiles, sessionToken) {
    if (issueFiles.length === 0) {
        const sessionTokenElement = document.querySelector('[id$="session_token"]');
        if (sessionTokenElement) {
            sessionTokenElement.setAttribute("value", sessionToken);
            sessionToken = '';
            // window.setTimeout(() => {
            //     singleCaptchaFn();
            // }, 1000);
            document.getElementById("transfer-form").submit();
        } else {
            console.error('Could not find any input id matching "session_token" on the page!');
        }
    } else if (issueFiles.length === dropzoneInstance.files.length) {
        alert('There are one or more files that could not be uploaded. Remove these files and try again.');
    }
}

export function updateDropMessageVisibility(dropzoneInstance) {
    const dropMessage = document.querySelector('.dz-message');
    dropMessage.style.display = dropzoneInstance.files.length === 0 ? 'block' : 'none';
}