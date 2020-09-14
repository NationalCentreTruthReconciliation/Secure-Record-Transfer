// Controls for Dropzone form on transfer page.

/**
 * Get a cookie's value by its name.
 * @param {*} name The name of the cookie to retrieve from the user
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
 * Appends an error message to the page in the dropzone-errors element. Multiple error messages are
 * allowed.
 * @param {string} errorMessage The error message to show
 */
function addDropzoneError(errorMessage) {
    errorZone = document.getElementById('dropzone-errors')
    newError = document.createElement('div')
    newError.className = 'field-error'
    newError.innerHTML = errorMessage
    errorZone.appendChild(newError)
}


/**
 * Removes all errors shown in the dropzone-errors element.
 */
function clearDropzoneErrors() {
    errorZone = document.getElementById('dropzone-errors')
    while (errorZone.lastElementChild) {
        errorZone.removeChild(errorZone.lastElementChild);
    }
}

Dropzone.autoDiscover = false
issueFiles = []
sessionToken = ''

// After page loads:
$(() => {
    $("#file-dropzone").dropzone({
        url: "/transfer/uploadfile/",
        paramName: "upload_files",
        addRemoveLinks: true,
        autoProcessQueue: false,
        autoQueue: true,
        uploadMultiple: true,
        parallelUploads: 2,
        maxFiles: 80,
        maxFilesize: 1024,
        timeout: 180000,
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
        init: function() {
            issueFiles = []
            dropzoneClosure = this
            submitButton = document.getElementById("submit-form-btn")

            submitButton.addEventListener("click", (event) => {
                event.preventDefault()
                event.stopPropagation()
                clearDropzoneErrors()

                if (dropzoneClosure.getQueuedFiles().length > 0) {
                    dropzoneClosure.options.autoProcessQueue = true
                    dropzoneClosure.processQueue()
                } else {
                    addDropzoneError('You cannot submit a form without files.')
                }
            });

            // Triggers on non-200 status
            this.on("error", (file, response, xhr) => {
                if ("verboseError" in response) {
                    addDropzoneError(response.verboseError)
                }
                else {
                    addDropzoneError(response.error)
                }
                issueFiles.push(file.name)
                document.getElementById("submit-form-btn").disabled = true
                dropzoneClosure.options.autoProcessQueue = false
            })

            this.on("addedfile", (file) => {
                clearDropzoneErrors()
            })

            this.on("removedfile", (file) => {
                // If this file previously caused an issue, remove it from issueFiles
                issueIndex = issueFiles.indexOf(file.name)
                if (issueIndex > -1) {
                    issueFiles.splice(issueIndex, 1)
                }

                if (issueFiles.length === 0) {
                    document.getElementById("submit-form-btn").disabled = false
                }
            })

            this.on("sendingmultiple", (file, xhr, formData) => {
                xhr.setRequestHeader("Upload-Session-Token", sessionToken)
            })

            this.on("successmultiple", (file, response) => {
                sessionToken = response['upload_session_token']
            })

            this.on("queuecomplete", () => {
                if (issueFiles.length === 0) {
                    var sessionTokenElement = document.querySelector('[id$="session_token"]')
                    if (sessionTokenElement) {
                        sessionTokenElement.setAttribute("value", sessionToken)
                        sessionToken = ''
                        // Show the end of the dropzone animation by delaying submission
                        window.setTimeout(() => {
                            document.getElementById("transfer-form").submit()
                        }, 1000)
                    }
                    else {
                        console.error('Could not find any input id matching "session_token" on the page!')
                    }
                }
                else {
                    alert('There are one or more files that could not be uploaded. Remove these files and try again.')
                }
            })
        }
    })
})
