import Dropzone from "dropzone";
import { clearDropzoneErrors, getCookie } from "./utils.js";
import { maxTotalUploadSize, maxSingleUploadSize, maxTotalUploadCount, maxTotalUploadSizeBytes } from "./config.js";
import {
    handleFileAdded,
    handleFileRemoved,
    handleError,
    handleSuccess,
    handleQueueComplete,
    updateDropMessageVisibility
} from "./dropzoneHandlers.js";

Dropzone.autoDiscover = false;

$(() => {
    let totalSizeBytes = 0;
    const csrfToken = getCookie('csrftoken');
    const submitButton = document.getElementById("submit-form-btn");

    function updateTotalSize(file, operation) {
        let changed = false;
        if (operation === '+') {
            totalSizeBytes += file.size;
            changed = true;
        } else if (operation === '-') {
            totalSizeBytes -= file.size;
            changed = true;
        }
        if (changed) {
            const totalSizeElement = document.getElementById('total-size');
            if (totalSizeElement) {
                const totalMiB = parseFloat((totalSizeBytes / (1024 * 1024)).toFixed(2));
                totalSizeElement.innerHTML = totalMiB;
                if (totalSizeBytes > maxTotalUploadSizeBytes) {
                    totalSizeElement.classList.add('field-error');
                } else {
                    totalSizeElement.classList.remove('field-error');
                }
            }

            const remainingSizeElement = document.getElementById('remaining-size');
            if (remainingSizeElement) {
                const remaining = maxTotalUploadSizeBytes - totalSizeBytes;
                if (remaining < 0) {
                    remainingSizeElement.innerHTML = '0';
                    remainingSizeElement.classList.add('field-error');
                } else {
                    const remainingMiB = parseFloat((remaining / (1024 * 1024)).toFixed(2));
                    remainingSizeElement.innerHTML = remainingMiB;
                    remainingSizeElement.classList.remove('field-error');
                }
            }
        }
    }

    $("#file-dropzone").dropzone({
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
            "X-CSRFToken": csrfToken,
        },
        accept: function (file, done) {
            if (totalSizeBytes > maxTotalUploadSizeBytes) {
                done({ 'error': `Maximum total upload size (${maxTotalUploadSize} MiB) exceeded` });
            } else if (this.files.length > this.options.maxFiles) {
                done({ 'error': 'You cannot upload any more files.' });
            } else if (this.files.slice(0, -1).map(f => f.name).includes(file.name)) {
                done({ 'error': 'You cannot upload two files with the same name.' });
            } else {
                $.post({
                    url: '/transfer/checkfile/',
                    data: { 'filename': file.name, 'filesize': file.size },
                    dataType: 'json',
                    headers: { 'X-CSRFToken': csrfToken },
                    success: function (response) {
                        if (response.accepted) {
                            done();
                        } else {
                            done(response);
                        }
                    },
                    error: function (xhr) {
                        if (xhr.responseJSON) {
                            done(xhr.responseJSON);
                        } else {
                            done({ 'error': `${xhr.status}: ${xhr.statusText}`, 'verboseError': undefined });
                        }
                    }
                });
            }
        },
        init: function () {
            this.issueFiles = [];
            this.uploadedFiles = [];
            this.sessionToken = '';

            updateDropMessageVisibility(this);

            this.on("addedfile", (file) => handleFileAdded(this, file, updateTotalSize));
            this.on("removedfile", (file) => handleFileRemoved(this, file, updateTotalSize, submitButton));
            this.on("error", (file, response) => handleError(file, response, submitButton, this));
            this.on("successmultiple", (files, response) => handleSuccess(files, response, this));
            this.on("queuecomplete", () => handleQueueComplete(this));

            submitButton.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();

                if (this.issueFiles.length > 0) {
                    alert('One or more files cannot be uploaded. Remove them before submitting');
                } else {
                    clearDropzoneErrors();
                    this.element.classList.remove('dz-submit-disabled');
                    if (this.getQueuedFiles().length + this.uploadedFiles.length === 0) {
                        alert('You cannot submit a form without files. Please choose at least one file');
                    } else {
                        this.options.autoProcessQueue = true;
                        this.processQueue();
                    }
                }
            });

            this.on("sendingmultiple", (file, xhr) => {
                xhr.setRequestHeader("Upload-Session-Token", this.sessionToken);
            });

            this.on("errormultiple", (files, response) => {
                if (response.uploadSessionToken) {
                    this.sessionToken = response.uploadSessionToken;
                }
                if (response.fatalError) {
                    window.location.href = response.redirect;
                }
            });
        }
    });
});