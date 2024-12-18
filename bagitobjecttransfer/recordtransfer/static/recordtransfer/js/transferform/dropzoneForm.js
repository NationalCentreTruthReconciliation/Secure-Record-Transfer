import Dropzone from "dropzone";

/**
 * Functions and configuration for Dropzone.
 */

Dropzone.autoDiscover = false

/**
 * Get a cookie's value by its name.
 * @param {String} name The name of the cookie to retrieve from the user
 * @returns {String} The cookie value. null if it does not exist
 */
function getCookie(name) {
    var cookieValue = null
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';')
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim()
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

/**
 * Appends an error message to the page in the dropzone-errors element.
 * @param {String} errorMessage The error message to show
 */
function addDropzoneError(errorMessage) {
    const errorZone = document.getElementById('dropzone-errors')
    const newError = document.createElement('div')
    newError.className = 'field-error'
    newError.innerHTML = errorMessage
    errorZone.appendChild(newError)
}

/**
 * Removes all errors shown in the dropzone-errors element.
 */
function clearDropzoneErrors() {
    const errorZone = document.getElementById('dropzone-errors')
    while (errorZone.lastElementChild) {
        errorZone.removeChild(errorZone.lastElementChild);
    }
}

$(() => {
    var issueFiles = []    // An array of file names
    var uploadedFiles = [] // An array of File objects
    var totalSizeBytes = 0
    var sessionToken = ''
    const csrfToken = getCookie('csrftoken')
    var dropMessage = document.querySelector('.dz-message'); // Custom drop message

    var maxTotalUploadSize = 256.00
    if (typeof (MAX_TOTAL_UPLOAD_SIZE) !== 'undefined') {
        maxTotalUploadSize = MAX_TOTAL_UPLOAD_SIZE
    }
    var maxTotalUploadSizeBytes = maxTotalUploadSize * 1024 * 1024

    var maxSingleUploadSize = 64.00
    if (typeof (MAX_SINGLE_UPLOAD_SIZE) !== 'undefined') {
        maxSingleUploadSize = MAX_SINGLE_UPLOAD_SIZE
    }

    var maxTotalUploadCount = 40
    if (typeof (MAX_TOTAL_UPLOAD_COUNT) !== 'undefined') {
        maxTotalUploadCount = MAX_TOTAL_UPLOAD_COUNT
    }

    // Update total size of all uploads in dropzone area
    function updateTotalSize(file, operation) {
        let changed = false
        if (operation === '+') {
            totalSizeBytes += file.size
            changed = true
        }
        else if (operation === '-') {
            totalSizeBytes -= file.size
            changed = true
        }
        if (changed) {
            var totalSizeElement = document.getElementById('total-size')
            if (totalSizeElement) {
                let totalMiB = parseFloat((totalSizeBytes / (1024 * 1024)).toFixed(2))
                totalSizeElement.innerHTML = totalMiB
                if (totalSizeBytes > maxTotalUploadSizeBytes) {
                    totalSizeElement.classList.add('field-error')
                }
                else {
                    totalSizeElement.classList.remove('field-error')
                }
            }

            var remainingSizeElement = document.getElementById('remaining-size')
            if (remainingSizeElement) {
                let remaining = maxTotalUploadSizeBytes - totalSizeBytes
                if (remaining < 0) {
                    remainingSizeElement.innerHTML = '0'
                    remainingSizeElement.classList.add('field-error')
                }
                else {
                    let remainingMiB = parseFloat((remaining / (1024 * 1024)).toFixed(2))
                    remainingSizeElement.innerHTML = remainingMiB
                    remainingSizeElement.classList.remove('field-error')
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
        // Hit endpoint to determine if a file can be uploaded
        accept: function (file, done) {
            if (totalSizeBytes > maxTotalUploadSizeBytes) {
                done({
                    'error': 'Maximum total upload size (' + maxTotalUploadSize + ' MiB) exceeded'
                })
            }
            else if (this.files.length > this.options.maxFiles) {
                done({
                    'error': 'You can not upload anymore files.'
                })
            }
            else if (this.files.slice(0, -1).map(f => f.name).includes(file.name)) {
                done({
                    'error': 'You can not upload two files with the same name.'
                })
            }
            else {
                $.post({
                    url: '/transfer/checkfile/',
                    data: {
                        'filename': file.name,
                        'filesize': file.size,
                    },
                    dataType: 'json',
                    headers: { 'X-CSRFToken': csrfToken },
                    success: function (response) {
                        if (response.accepted) {
                            done()
                        }
                        else {
                            done(response)
                        }
                    },
                    error: function (xhr, status, error) {
                        if (xhr.responseJSON) {
                            done(xhr.responseJSON)
                        }
                        else {
                            done({
                                'error': xhr.status + ': ' + xhr.statusText,
                                'verboseError': undefined,
                            })
                        }
                    }
                })
            }
        },
        init: function () {
            issueFiles = []
            uploadedFiles = []
            sessionToken = ''

            var dropzoneClosure = this
            var submitButton = document.getElementById("submit-form-btn")

            // Function to update the visibility of the drop message
            function updateDropMessageVisibility() {
                if (dropzoneClosure.files.length === 0) {
                    dropMessage.style.display = 'block'; // Show message when no files are present
                } else {
                    dropMessage.style.display = 'none'; // Hide message when there are files
                }
            }

            // Call on initialization to set the correct state
            updateDropMessageVisibility();

            // Update drop message visibility when files are added or removed
            this.on("addedfile", function () {
                updateDropMessageVisibility();
            });

            this.on("removedfile", function () {
                updateDropMessageVisibility();
            });

            submitButton.addEventListener("click", (event) => {
                event.preventDefault()
                event.stopPropagation()

                if (issueFiles.length > 0) {
                    alert('One or more files cannot be uploaded. Remove them before submitting')
                }
                else {
                    clearDropzoneErrors()
                    this.element.classList.remove('dz-submit-disabled')
                    if (dropzoneClosure.getQueuedFiles().length + uploadedFiles.length === 0) {
                        alert('You cannot submit a form without files. Please choose at least one file')
                    }
                    else {
                        dropzoneClosure.options.autoProcessQueue = true
                        dropzoneClosure.processQueue()
                    }
                }
            })

            // Triggers on non-200 status
            this.on("error", (file, response, xhr) => {
                if (response.verboseError) {
                    addDropzoneError(response.verboseError)
                }
                else if (response.error) {
                    addDropzoneError(response.error)
                }
                else {
                    addDropzoneError(response)
                }

                issueFiles.push(file.name)
                document.getElementById("submit-form-btn").disabled = true
                this.element.classList.add('dz-submit-disabled')
                dropzoneClosure.options.autoProcessQueue = false
            })

            this.on("addedfile", (file) => {
                updateTotalSize(file, '+')
            })

            this.on("removedfile", (file) => {
                updateTotalSize(file, '-')

                // If this file previously caused an issue, remove it from issueFiles
                issueIndex = issueFiles.indexOf(file.name)
                if (issueIndex > -1) {
                    issueFiles.splice(issueIndex, 1)
                }
                if (issueFiles.length === 0) {
                    document.getElementById("submit-form-btn").disabled = false
                    clearDropzoneErrors()
                    this.element.classList.remove('dz-submit-disabled')
                }
            })

            this.on("sendingmultiple", (file, xhr, formData) => {
                xhr.setRequestHeader("Upload-Session-Token", sessionToken)
            })

            this.on("successmultiple", (files, response) => {
                if (response.uploadSessionToken) {
                    sessionToken = response.uploadSessionToken
                }
                var invalidFileNames = []
                for (const issue of response.issues) {
                    var fileName = issue.file
                    invalidFileNames.push(fileName)
                    var fileObj = files.filter(file => { return file.name === fileName })[0]
                    var errMessage = { 'error': issue.error, 'verboseError': issue.verboseError }
                    dropzoneClosure.emit('error', fileObj, errMessage, null)
                }
                for (const file of files) {
                    if (invalidFileNames && invalidFileNames.indexOf(file.name) === -1) {
                        uploadedFiles.push(file)
                    }
                }
            })

            this.on("errormultiple", (files, response) => {
                if (response.uploadSessionToken) {
                    sessionToken = response.uploadSessionToken
                }
                if (response.fatalError) {
                    window.location.href = response.redirect
                }
            })

            this.on("queuecomplete", () => {
                if (issueFiles.length === 0) {
                    var sessionTokenElement = document.querySelector('[id$="session_token"]')
                    if (sessionTokenElement) {
                        sessionTokenElement.setAttribute("value", sessionToken)
                        sessionToken = ''
                        // Show the end of the dropzone animation by delaying submission
                        window.setTimeout(() => {
                            // Use this function to execute the invisible Captcha methods.
                            singleCaptchaFn();
                        }, 1000)
                    }
                    else {
                        console.error('Could not find any input id matching "session_token" on the page!')
                    }
                }
                else if (!issueFiles.length === dropzoneClosure.files.length) {
                    alert('There are one or more files that could not be uploaded. Remove these files and try again.')
                }
            })
        }
    })
})
