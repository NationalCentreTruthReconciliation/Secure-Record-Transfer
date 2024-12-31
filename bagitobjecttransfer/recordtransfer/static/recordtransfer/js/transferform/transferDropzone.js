import Dropzone from "dropzone";
import { clearDropzoneErrors, getCookie } from "./utils.js";
import { maxTotalUploadSize, maxSingleUploadSize, maxTotalUploadCount, maxTotalUploadSizeBytes } from "./config.js";

Dropzone.autoDiscover = false;

export class TransferDropzone extends Dropzone {
    constructor(element) {
        super(element, {
            url: "/transfer/uploadfile/",
            paramName: "upload_files",
            addRemoveLinks: true,
            autoProcessQueue: false,
            autoQueue: true,
            uploadMultiple: true,
            parallelUploads: 2,
            maxFiles: maxTotalUploadCount,
            maxFilesize: maxSingleUploadSize,
            filesizeBase: 1024,
            dictFileSizeUnits: { tb: "TiB", gb: "GiB", mb: "MiB", kb: "KiB", b: "b" },
            timeout: 180000,
            headers: {
                "X-CSRFToken": getCookie('csrftoken'),
            }
        });
        this.options.init = this.init;
    }

    init = () => {
        this.totalSizeBytes = 0;
        this.issueFiles = [];
        this.uploadedFiles = [];
        this.sessionToken = '';
        this.submitButton = document.getElementById("submit-form-btn");
        this.dropMessage = document.querySelector('.dz-message');
        this.setupEventListeners();
        this.updateDropMessageVisibility();
    }

    setupEventListeners = () => {
        this.on("addedfile", (file) => this.handleAddedFile(file));
        this.on("removedfile", (file) => this.handleRemovedFile(file));
        this.on("successmultiple", (files, response) => this.handleSuccessMultiple(files, response));
        this.on("queuecomplete", () => this.handleQueueComplete());
        this.on("sendingmultiple", (files, xhr) => this.handleSendingMultiple(files, xhr));
        this.on("errormultiple", (files, response) => this.handleErrorMultiple(files, response));
        this.submitButton.addEventListener("click", (event) => this.handleSubmit(event));
    }

    updateTotalSize = (file, operation) => {
        let changed = false;
        if (operation === '+') {
            this.totalSizeBytes += file.size;
            changed = true;
        } else if (operation === '-') {
            this.totalSizeBytes -= file.size;
            changed = true;
        }
        if (changed) {
            this.updateSizeDisplay();
        }
    }

    updateSizeDisplay = () => {
        const totalSizeElement = document.getElementById('total-size');
        const remainingSizeElement = document.getElementById('remaining-size');

        if (totalSizeElement) {
            const totalMiB = parseFloat((this.totalSizeBytes / (1024 * 1024)).toFixed(2));
            totalSizeElement.innerHTML = totalMiB;
            totalSizeElement.classList.toggle('field-error', this.totalSizeBytes > maxTotalUploadSizeBytes);
        }

        if (remainingSizeElement) {
            const remaining = maxTotalUploadSizeBytes - this.totalSizeBytes;
            const remainingMiB = remaining < 0 ? 0 : parseFloat((remaining / (1024 * 1024)).toFixed(2));
            remainingSizeElement.innerHTML = remainingMiB;
            remainingSizeElement.classList.toggle('field-error', remaining < 0);
        }
    }

    accept(file, done) {
        if (this.totalSizeBytes > maxTotalUploadSizeBytes) {
            done({ error: `Maximum total upload size (${maxTotalUploadSize} MiB) exceeded` });
            return;
        }
        if (this.files.length > this.options.maxFiles) {
            done({ error: 'You cannot upload any more files.' });
            return;
        }
        if (this.files.slice(0, -1).map(f => f.name).includes(file.name)) {
            done({ error: 'You cannot upload two files with the same name.' });
            return;
        }

        fetch('/transfer/checkfile/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.options.headers["X-CSRFToken"]
            },
            body: JSON.stringify({
                filename: file.name,
                filesize: file.size
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.accepted) {
                done(data);
            } else {
                done();
            }
        })
        .catch(error => {
            done({ error: error.message || 'Upload failed' });
        });
    }

    // // Event handlers

    handleAddedFile = (file) => {
        this.updateTotalSize(file, '+');
        this.updateDropMessageVisibility();
    }

    handleRemovedFile = (file) => {
        this.updateTotalSize(file, '-');
        this.updateDropMessageVisibility();
    }

    handleSuccessMultiple = (files, response) => {
        if (response.uploadSessionToken) {
            this.sessionToken = response.uploadSessionToken
        }
        var invalidFileNames = []
        for (const issue of response.issues) {
            var fileName = issue.file
            invalidFileNames.push(fileName)
            var fileObj = files.filter(file => { return file.name === fileName })[0]
            var errMessage = { 'error': issue.error, 'verboseError': issue.verboseError }
            this.emit('error', fileObj, errMessage, null)
        }
        for (const file of files) {
            if (invalidFileNames && invalidFileNames.indexOf(file.name) === -1) {
                uploadedFiles.push(file)
            }
        }
    }

    handleSendingMultiple = (_files, xhr) => {
        xhr.setRequestHeader("Upload-Session-Token", this.sessionToken);
    }

    handleErrorMultiple = (_files, response) => {
        if (response.uploadSessionToken) {
            this.sessionToken = response.uploadSessionToken;
        }
        if (response.fatalError) {
            window.location.href = response.redirect;
        }
    }

    handleQueueComplete = () => {
        if (this.issueFiles.length === 0) {
            const sessionTokenElement = document.querySelector('[id$="session_token"]');
            if (sessionTokenElement) {
                sessionTokenElement.setAttribute("value", this.sessionToken);
                this.sessionToken = '';
                document.getElementById("transfer-form").submit();
            } else {
                console.error('Could not find any input id matching "session_token" on the page!');
            }
        } else {
            alert('There are one or more files that could not be uploaded. Remove these files and try again.');
        }
    }

    handleSubmit = (event) => {
        event.preventDefault();
        event.stopPropagation();

        if (this.issueFiles.length > 0) {
            alert('One or more files cannot be uploaded. Remove them before submitting');
            return;
        }

        clearDropzoneErrors();
        this.element.classList.remove('dz-submit-disabled');
        
        if (this.getQueuedFiles().length + this.uploadedFiles.length === 0) {
            alert('You cannot submit a form without files. Please choose at least one file');
            return;
        }

        this.options.autoProcessQueue = true;
        this.processQueue();
    }

    updateDropMessageVisibility = () => {
        if (this.files.length === 0) {
            // Show message when no files are present
            this.dropMessage.style.display = 'block'; 
        } else {
            // Hide message when there are files
            this.dropMessage.style.display = 'none';
        }
    }
}