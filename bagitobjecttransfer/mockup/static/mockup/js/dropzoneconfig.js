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

$(() => {
    $("#file_dropzone").dropzone({
        url: "/transfer/uploadfile/",
        paramName: "upload_files",
        addRemoveLinks: true,
        autoProcessQueue: false,
        uploadMultiple: true,
        parallelUploads: 5,
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
                    dropzoneClosure.processQueue();
                } else {
                    alert("You cannot submit a form without any files.")
                }
            });

            this.on("successmultiple", function(files, response) {
                setTimeout(function () {
                    document.getElementById("transfer-form").submit()
                }, 1000)
            })
        }
    })
})