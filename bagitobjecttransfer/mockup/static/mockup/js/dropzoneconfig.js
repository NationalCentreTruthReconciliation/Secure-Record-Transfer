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


function addDropzoneError(errorMessage) {
    errorZone = document.getElementById('dropzone-errors')
    newError = document.createElement('div')
    newError.className = 'field-error'
    newError.innerHTML = errorMessage
    errorZone.appendChild(newError)
}


function clearDropzoneErrors() {
    errorZone = document.getElementById('dropzone-errors')
    while (errorZone.lastElementChild) {
        errorZone.removeChild(errorZone.lastElementChild);
    }
}


Dropzone.autoDiscover = false
issueFiles = []
sessionToken = ''

$(() => {
    $("#file-dropzone").dropzone({
        url: "/transfer/uploadfile/",
        paramName: "upload_files",
        addRemoveLinks: true,
        autoProcessQueue: false,
        uploadMultiple: true,
        parallelUploads: 2,
        maxFiles: 80,
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

            this.on("error", (file, response, xhr) => {
                console.error(response.error)
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
                    var hiddenTokenInput = document.getElementById("id_session_token")
                    if (hiddenTokenInput !== null) {
                        hiddenTokenInput.setAttribute("value", sessionToken)
                        sessionToken = ''
                        // Show the end of the dropzone animation by delaying submission
                        window.setTimeout(() => {
                            document.getElementById("transfer-form").submit()
                        }, 1000)
                    }
                    else {
                        console.error('Could not find the hidden JSON input field on the page!')
                    }
                }
                else {
                    alert('There are one or more files that could not be uploaded. Remove these files and try again.')
                }
            })
        }
    })
})