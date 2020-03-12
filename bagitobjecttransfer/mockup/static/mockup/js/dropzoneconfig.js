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

Dropzone.autoDiscover = false
fileList = []
issueFiles = []

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
            fileList = []
            issueFiles = []
            dropzoneClosure = this
            submitButton = document.getElementById("submit-form-btn")

            submitButton.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (dropzoneClosure.getQueuedFiles().length > 0) {
                    dropzoneClosure.options.autoProcessQueue = true
                    dropzoneClosure.processQueue();
                } else {
                    // TODO: Don't use alert. Add error to webpage
                    alert("You cannot submit a form without any files.")
                }
            });

            this.on("error", (file, response, xhr) => {
                console.error(response.error)
                issueFiles.push(file.name)
                document.getElementById("submit-form-btn").disabled = true
                dropzoneClosure.options.autoProcessQueue = false
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

            this.on("successmultiple", (file, response) => {
                for (var i = 0; i < response.files.length; i++) {
                    fileList.push(response.files[i])
                }
            })

            this.on("queuecomplete", () => {
                if (issueFiles.length === 0) {
                    var hiddenJsonInput = document.getElementById("id_file_list_json")
                    if (hiddenJsonInput !== null) {
                        hiddenJsonInput.setAttribute("value", JSON.stringify(fileList))
                        fileList = []
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