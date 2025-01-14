/**
 * Functions and configuration for Dropzone.
 */
import Dropzone from "dropzone";

Dropzone.autoDiscover = false;

/**
 * Get a cookie's value by its name.
 * @param {string} name The name of the cookie to retrieve from the user
 * @returns {string} The cookie value. null if it does not exist
 */
function getCookie(name) {
    if (!document.cookie || document.cookie === "") {
        return null;
    }

    const cookies = document.cookie.split(";");
    const targetCookie = cookies
        .map(cookie => cookie.trim())
        .find(cookie => cookie.startsWith(`${name}=`));

    if (!targetCookie) {
        return null;
    }

    return decodeURIComponent(targetCookie.substring(name.length + 1));
}

/**
 * Appends an error message to the page in the dropzone-errors element.
 * @param {string} errorMessage The error message to show
 */
function addDropzoneError(errorMessage) {
    const errorZone = document.getElementById("dropzone-errors");
    const newError = document.createElement("div");
    newError.className = "field-error";
    newError.innerHTML = errorMessage;
    errorZone.appendChild(newError);
}

/**
 * Removes all errors shown in the dropzone-errors element.
 */
function clearDropzoneErrors() {
    const errorZone = document.getElementById("dropzone-errors");
    while (errorZone.lastElementChild) {
        errorZone.removeChild(errorZone.lastElementChild);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    var issueFiles = [];    // An array of file names
    var uploadedFiles = []; // An array of File objects
    var totalSizeBytes = 0;
    var sessionToken = "";
    const csrfToken = getCookie("csrftoken");
    const dropMessage = document.querySelector(".dz-message"); // Custom drop message

    // Context injected from template
    const dropzoneContextElement = document.getElementById("py_context_dropzone");
    const dropzoneContext = JSON.parse(dropzoneContextElement?.textContent || "{}");
    const maxSingleUploadSize = (dropzoneContext?.max_single_upload_size ?? 64.00).toFixed(2);
    const maxTotalUploadCount = dropzoneContext?.max_total_upload_count ?? 40;
    const maxTotalUploadSize = (dropzoneContext?.max_total_upload_size ?? 256.00).toFixed(2);
    const maxTotalUploadSizeBytes = maxTotalUploadSize * 1024 * 1024;

    // Update total size of all uploads in dropzone area
    /**
     *
     * @param file
     * @param operation
     */
    function updateTotalSize(file, operation) {
        let changed = false;
        if (operation === "+") {
            totalSizeBytes += file.size;
            changed = true;
        }
        else if (operation === "-") {
            totalSizeBytes -= file.size;
            changed = true;
        }
        if (changed) {
            var totalSizeElement = document.getElementById("total-size");
            if (totalSizeElement) {
                const totalMiB = parseFloat((totalSizeBytes / (1024 * 1024)).toFixed(2));
                totalSizeElement.innerHTML = totalMiB;
                if (totalSizeBytes > maxTotalUploadSizeBytes) {
                    totalSizeElement.classList.add("field-error");
                }
                else {
                    totalSizeElement.classList.remove("field-error");
                }
            }

            var remainingSizeElement = document.getElementById("remaining-size");
            if (remainingSizeElement) {
                const remaining = maxTotalUploadSizeBytes - totalSizeBytes;
                if (remaining < 0) {
                    remainingSizeElement.innerHTML = "0";
                    remainingSizeElement.classList.add("field-error");
                }
                else {
                    const remainingMiB = parseFloat((remaining / (1024 * 1024)).toFixed(2));
                    remainingSizeElement.innerHTML = remainingMiB;
                    remainingSizeElement.classList.remove("field-error");
                }
            }
        }
    }

    new Dropzone("#file-dropzone", {
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
        // Hit endpoint to determine if a file can be uploaded
        accept: function (file, done) {
            if (totalSizeBytes > maxTotalUploadSizeBytes) {
                done({
                    "error": `Maximum total upload size (${maxTotalUploadSize} MiB) exceeded`
                });
            }
            else if (this.files.length > this.options.maxFiles) {
                done({
                    "error": "You can not upload anymore files."
                });
            }
            else if (this.files.slice(0, -1).map(f => f.name).includes(file.name)) {
                done({
                    "error": "You can not upload two files with the same name."
                });
            }
            else {
                const params = new URLSearchParams({
                    filename: file.name,
                    filesize: file.size
                });

                fetch(`/transfer/checkfile/?${params.toString()}`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken,
                    }
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.accepted) {
                            done();
                        } else {
                            done(data);
                        }
                    })
                    .catch(error => {
                        if (error.response?.json) {
                            done(error.response.json);
                        } else {
                            done({
                                "error": `${error.status || "Error"}: ${error.statusText || "Unknown error"}`,
                                "verboseError": undefined,
                            });
                        }
                    });
            }
        },
        init: function () {
            issueFiles = [];
            uploadedFiles = [];
            sessionToken = "";

            var dropzoneClosure = this;
            var submitButton = document.getElementById("submit-form-btn");

            // Function to update the visibility of the drop message
            function updateDropMessageVisibility() {
                if (dropzoneClosure.files.length === 0) {
                    dropMessage.style.display = "block"; // Show message when no files are present
                } else {
                    dropMessage.style.display = "none"; // Hide message when there are files
                }
            }

            // Call on initialization to set the correct state
            updateDropMessageVisibility();

            // Update drop message visibility when files are added or removed
            this.on("addedfile", function() {
                updateDropMessageVisibility();
            });

            this.on("removedfile", function() {
                updateDropMessageVisibility();
            });

            submitButton.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();

                if (issueFiles.length > 0) {
                    alert("One or more files cannot be uploaded. Remove them before submitting");
                }
                else {
                    clearDropzoneErrors();
                    this.element.classList.remove("dz-submit-disabled");
                    if (dropzoneClosure.getQueuedFiles().length + uploadedFiles.length === 0) {
                        alert("You cannot submit a form without files. Please choose at least one file");
                    }
                    else {
                        dropzoneClosure.options.autoProcessQueue = true;
                        dropzoneClosure.processQueue();
                    }
                }
            });

            // Call on initialization to set the correct state
            updateDropMessageVisibility();

            // Update drop message visibility when files are added or removed
            this.on("addedfile", function (file) {
                updateTotalSize(file, "+");
                updateDropMessageVisibility();
            });

            this.on("removedfile", function (file) {
                updateTotalSize(file, "-");

                // If this file previously caused an issue, remove it from issueFiles
                const issueIndex = issueFiles.indexOf(file.name);
                if (issueIndex > -1) {
                    issueFiles.splice(issueIndex, 1);
                }
                if (issueFiles.length === 0) {
                    document.getElementById("submit-form-btn").disabled = false;
                    clearDropzoneErrors();
                    this.element.classList.remove("dz-submit-disabled");
                }

                updateDropMessageVisibility();
            });

            // Triggers on non-200 status
            this.on("error", (file, response, xhr) => {
                if (response.verboseError) {
                    addDropzoneError(response.verboseError);
                }
                else if (response.error) {
                    addDropzoneError(response.error);
                }
                else {
                    addDropzoneError(response);
                }

                issueFiles.push(file.name);
                document.getElementById("submit-form-btn").disabled = true;
                this.element.classList.add("dz-submit-disabled");
                dropzoneClosure.options.autoProcessQueue = false;
            });

            this.on("sendingmultiple", (file, xhr, formData) => {
                xhr.setRequestHeader("Upload-Session-Token", sessionToken);
            });

            this.on("successmultiple", (files, response) => {
                if (response.uploadSessionToken) {
                    sessionToken = response.uploadSessionToken;
                }
                var invalidFileNames = [];
                for (const issue of response.issues) {
                    var fileName = issue.file;
                    invalidFileNames.push(fileName);
                    var fileObj = files.filter(file => { return file.name === fileName; })[0];
                    var errMessage = { "error": issue.error, "verboseError": issue.verboseError };
                    dropzoneClosure.emit("error", fileObj, errMessage, null);
                }
                for (const file of files) {
                    if (invalidFileNames && invalidFileNames.indexOf(file.name) === -1) {
                        uploadedFiles.push(file);
                    }
                }
            });

            this.on("errormultiple", (files, response) => {
                if (response.uploadSessionToken) {
                    sessionToken = response.uploadSessionToken;
                }
                if (response.fatalError) {
                    window.location.href = response.redirect;
                }
            });

            this.on("queuecomplete", () => {
                if (issueFiles.length === 0) {
                    var sessionTokenElement = document.querySelector("[id$=\"session_token\"]");
                    if (sessionTokenElement) {
                        sessionTokenElement.setAttribute("value", sessionToken);
                        sessionToken = "";
                        // Show the end of the dropzone animation by delaying submission
                        window.setTimeout(() => {
                            // Use this function to execute the invisible Captcha methods.
                            singleCaptchaFn();
                        }, 1000);
                    }
                    else {
                        console.error("Could not find any input id matching \"session_token\" on the page!");
                    }
                }
                else if (!issueFiles.length === dropzoneClosure.files.length) {
                    alert("There are one or more files that could not be uploaded. Remove these files and try again.");
                }
            });
        }
    });
});
