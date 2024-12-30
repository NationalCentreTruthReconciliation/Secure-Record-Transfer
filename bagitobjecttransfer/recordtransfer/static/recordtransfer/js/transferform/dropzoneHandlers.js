import { addDropzoneError, clearDropzoneErrors } from "./utils.js";

export function handleFileAdded(dropzoneInstance, file, updateTotalSize) {
    updateTotalSize(file, '+');
    updateDropMessageVisibility(dropzoneInstance);
}

export function handleFileRemoved(dropzoneInstance, file, updateTotalSize, submitButton) {
    updateTotalSize(file, '-');
    const issueIndex = dropzoneInstance.issueFiles.indexOf(file.name);
    if (issueIndex > -1) {
        dropzoneInstance.issueFiles.splice(issueIndex, 1);
    }
    if (dropzoneInstance.issueFiles.length === 0) {
        submitButton.disabled = false;
        clearDropzoneErrors();
        dropzoneInstance.element.classList.remove('dz-submit-disabled');
    }
    updateDropMessageVisibility(dropzoneInstance);
}

export function handleError(file, response, submitButton, dropzoneInstance) {
    addDropzoneError(response.verboseError || response.error || response);
    dropzoneInstance.issueFiles.push(file.name);
    submitButton.disabled = true;
    dropzoneInstance.element.classList.add('dz-submit-disabled');
    dropzoneInstance.options.autoProcessQueue = false;
}

export function handleSuccess(files, response, dropzoneInstance) {
    console.log("handleSuccess");
    if (response.uploadSessionToken) {
        dropzoneInstance.sessionToken = response.uploadSessionToken;
    }
    console.log("In handleSuccess, sessionToken is " + dropzoneInstance.sessionToken);
    const invalidFileNames = response.issues.map(issue => issue.file);
    invalidFileNames.forEach(fileName => {
        const fileObj = files.find(file => file.name === fileName);
        dropzoneInstance.emit('error', fileObj, { 'error': issue.error, 'verboseError': issue.verboseError }, null);
    });
    files.forEach(file => {
        if (!invalidFileNames.includes(file.name)) {
            dropzoneInstance.uploadedFiles.push(file);
        }
    });
}

export function handleQueueComplete(dropzoneInstance) {
    console.log("handleQueueComplete");
    if (dropzoneInstance.issueFiles.length === 0) {
        const sessionTokenElement = document.querySelector('[id$="session_token"]');
        if (sessionTokenElement) {
            console.log("In handleQueueComplete, sessionToken is " + dropzoneInstance.sessionToken);
            sessionTokenElement.setAttribute("value", dropzoneInstance.sessionToken);
            dropzoneInstance.sessionToken = '';
            // window.setTimeout(() => {
            //     singleCaptchaFn();
            // }, 1000);
            // document.getElementById("transfer-form").submit();
        } else {
            console.error('Could not find any input id matching "session_token" on the page!');
        }
    } else if (dropzoneInstance.issueFiles.length === dropzoneInstance.files.length) {
        alert('There are one or more files that could not be uploaded. Remove these files and try again.');
    }
}

export function updateDropMessageVisibility(dropzoneInstance) {
    const dropMessage = document.querySelector('.dz-message');
    dropMessage.style.display = dropzoneInstance.files.length === 0 ? 'block' : 'none';
}