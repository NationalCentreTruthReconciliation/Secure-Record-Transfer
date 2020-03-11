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
            dropzoneClosure = this
            submitButton = document.getElementById("submit-form-btn")

            submitButton.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (dropzoneClosure.getQueuedFiles().length > 0) {
                    dropzoneClosure.options.autoProcessQueue = true
                    dropzoneClosure.processQueue();
                } else {
                    alert("You cannot submit a form without any files.")
                }
            });

            this.on("successmultiple", (files, response) => {
                for (var i = 0; i < response.files.length; i++) {
                    fileList.push(response.files[i])
                }
            })

            this.on("queuecomplete", () => {
                var hiddenJsonInput = document.getElementById("id_file_list_json")
                if (hiddenJsonInput != null) {
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
            })
        }
    })
})