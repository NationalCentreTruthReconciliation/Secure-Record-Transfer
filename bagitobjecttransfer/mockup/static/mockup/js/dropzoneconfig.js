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
    $("#id_upload_files").dropzone({
        url: '/transfer/send/',
        paramName: 'upload_files',
        addRemoveLinks: true,
        autoProcessQueue: false,
        uploadMultiple: true,
        parallelUploads: 5,
        maxFiles: 80,
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        init: function() {
            dropzoneClosure = this
            document.getElementById('submit-transfer-form').addEventListener('click', function(event) {
                dropzoneClosure.processQueue()
            })
        }
    })
})
