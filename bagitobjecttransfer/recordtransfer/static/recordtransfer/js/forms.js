/**
 * Functions and configuration for Django forms and Dropzone.
 *
 * Credit to this article for adding/removing forms from formsets:
 * https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
 */


const VALID_INPUTS = 'input:not([type=button]):not([type=submit]):not([type=reset]), textarea'
const ID_NUM_REGEX = new RegExp('-(\\d+)-')
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
 * Test if an element exists on the page.
 * @param {String} selector A jQuery type selector string
 * @returns {Boolean} true if element exists, false otherwise
 */
function elementExists(selector) {
    return $(selector).length !== 0
}

/**
 * Get the prefix name of the currently activated formset.
 * @returns {String} The name of the formset
 */
function getFormPrefix() {
    if (elementExists('#id_rights-TOTAL_FORMS')) {
        return 'rights'
    }
    else if (elementExists('#id_otheridentifiers-TOTAL_FORMS')) {
        return 'otheridentifiers'
    }
    else {
        return 'none'
    }
}

/**
 * Get the current number of forms displayed on the page.
 * @param {String} prefix The form prefix, if it is known
 * @returns {Number} The current number of forms
 */
function getTotalForms(prefix = null) {
    var formPrefix = prefix === null ? getFormPrefix() : prefix
    return parseInt($(`#id_${formPrefix}-TOTAL_FORMS`).val())
}

/**
 * Get the maximum number of allowable forms set by the backend.
 * @param {String} prefix The form prefix, if it is known
 * @returns {Number} The maximum number of forms
 */
function getMaxForms(prefix = null) {
    var formPrefix = prefix === null ? getFormPrefix() : prefix
    return parseInt($(`#id_${formPrefix}-MAX_NUM_FORMS`).val())
}

/**
 * Add a new form to the formset by cloning the selected form. The cloned form is inserted in the
 * document tree directly below the form that was cloned. This function respects whether the
 * max_num of formsets was set in the backend.
 * @param {String} cloneFormSelector The form to clone to create a new form from
 */
function appendNewForm(cloneFormSelector) {
    var prefix = getFormPrefix()
    var totalForms = getTotalForms(prefix)
    var maxNumForms = getMaxForms(prefix)

    if (totalForms + 1 > maxNumForms) {
        alert(`You may not exceed ${maxNumForms} form sections.`)
        return
    }

    var newForm = $(cloneFormSelector).clone(true)
    newForm.addClass('margin-top-25px')
    incrementInputAttributes(newForm)
    incrementLabelAttributes(newForm)
    $(`#id_${prefix}-TOTAL_FORMS`).val(totalForms + 1);
    $(cloneFormSelector).after(newForm);
}

/**
 * Increment all of the indices for the input elements of a formset form
 * @param form The form row element selected by jQuery
 */
function incrementInputAttributes(form) {
    var formIdNumber = -1
    var oldNumber = null
    var newNumber = null

    $(form).find(VALID_INPUTS).each((_, element) => {
        var name = $(element).attr('name')

        if (formIdNumber === -1) {
            var match = ID_NUM_REGEX.exec(name)
            formIdNumber = parseInt(match[1])
            oldNumber = `-${formIdNumber}-`
            newNumber = `-${formIdNumber + 1}-`
        }

        var newName = name.replace(oldNumber, newNumber)
        var newId = `id_${newName}`

        $(element).attr({
            'name': newName,
            'id': newId
        })
        .val('')
        .removeAttr('checked')
    })
}

/**
 * Increment all of the indices for the label elements of a formset form
 * @param form The form row element selected by jQuery
 */
function incrementLabelAttributes(form) {
    var formIdNumber = -1
    var oldNumber = null
    var newNumber = null

    $(form).find('label').each((_, element) => {
        var forValue = $(element).attr('for')

        if (forValue) {
            if (formIdNumber === -1) {
                var match = ID_NUM_REGEX.exec(forValue)
                formIdNumber = parseInt(match[1])
                oldNumber = `-${formIdNumber}-`
                newNumber = `-${formIdNumber + 1}-`
            }

            var newForValue = forValue.replace(oldNumber, newNumber)
            $(element).attr({
                'for': newForValue
            })
        }
    })
}

/**
 * Delete a specific form element from the formset
 * @param {String} deleteFormSelector The selector for the form row
 */
function deleteForm(deleteFormSelector) {
    var prefix = getFormPrefix()
    var total = getTotalForms(prefix)

    if (total > 1) {
        $(deleteFormSelector).remove()

        var forms = $('.form-row')
        $(`#id_${prefix}-TOTAL_FORMS`).val(forms.length)

        // Update each input's index for the remaining forms
        for (var i = 0; i < forms.length; i++) {
            $(forms.get(i)).find(':input').each((_, element) => {
                updateElementIndex(element, i, prefix);
            });
        }
    }
}

/**
 * Update a form element's index within the current form.
 * @param element An element selected from the page with jQuery
 * @param {Number} index The new index the element is to have
 */
function updateElementIndex(element, index, prefix) {
    var idRegex = new RegExp(`(${prefix}-\\d+)`);
    var replacement = prefix + '-' + index;

    forValue = $(element).attr("for")
    if (forValue) {
        const new_for = forValue.replace(idRegex, replacement)
        $(element).attr({
            "for": new_for
        })
    }

    if (element.id) {
        element.id = element.id.replace(idRegex, replacement)
    }

    if (element.name) {
        element.name = element.name.replace(idRegex, replacement)
    }
}

/**
 * Appends an error message to the page in the dropzone-errors element.
 * @param {String} errorMessage The error message to show
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


/**
 * Show or hide div.flex-items related to form fields.
 * @param {Array} selectors Form field selectors, the closest div.flex-items will be shown/hidden
 * @param {String} state Shows divs if 'on', hides divs if 'off', does nothing otherwise
 */
function toggleFlexItems(selectors, state) {
    if (state === 'on') {
        selectors.forEach(function(sel) {
            $(sel).closest('div.flex-item').show()
        })
    }
    else if (state === 'off') {
        selectors.forEach(function(sel) {
            $(sel).closest('div.flex-item').hide()
        })
    }
}

$(() => {
    /***************************************************************************
     * Dropzone Setup
     **************************************************************************/
    var issueFiles = []
    var sessionToken = ''

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


    /***************************************************************************
     * Formset Setup
     **************************************************************************/
    var totalForms = getTotalForms()
    $('.remove-form-row').prop('disabled', Boolean(totalForms <= 1))

    $('.add-form-row').on('click', (event) => {
        event.preventDefault()
        appendNewForm('.form-row:last')
        totalForms = getTotalForms()
        $('.remove-form-row').prop('disabled', Boolean(totalForms <= 1))
    })

    $('.remove-form-row').on('click', (event) => {
        event.preventDefault()
        deleteForm('.form-row:last')
        totalForms = getTotalForms()
        $('.remove-form-row').prop('disabled', Boolean(totalForms <= 1))
    })

    $('.remove-form-row').hover(() => {
        totalForms = getTotalForms()
        if (totalForms > 1) {
            $('.form-row:last').find('label').each((_, element) => {
                $(element).addClass('red-text-strikethrough')
            })
            $('.form-row:last').find(VALID_INPUTS).each((_, element) => {
                $(element).addClass('red-border')
                $(element).addClass('red-text-strikethrough')
            })
        }
    }, () => {
        $('.form-row:last').find('label').each((_, element) => {
            $(element).removeClass('red-text-strikethrough')
        })
        $('.form-row:last').find(VALID_INPUTS).each((_, element) => {
            $(element).removeClass('red-border')
            $(element).removeClass('red-text-strikethrough')
        })
    })

    /***************************************************************************
     * Expandable Forms Setup
     **************************************************************************/
    const sourceInfoFlexItems = [
        '#id_sourceinfo-source_note',
        '#id_sourceinfo-custodial_history',
    ]

    const sourceInfoExpandButton = [
        '.add-extra-source-info'
    ]


    if (sourceInfoFlexItems.some((selector) => elementExists(selector))) {
        let dirtySourceInfo = (
            $('#id_sourceinfo-source_note').val() ||
            $('#id_sourceinfo-custodial_history').val()
        )
        let fieldState = dirtySourceInfo ? 'on' : 'off'
        let buttonState = dirtySourceInfo ? 'off' : 'on'
        toggleFlexItems(sourceInfoFlexItems, fieldState)
        toggleFlexItems(sourceInfoExpandButton, buttonState)

        $('.add-extra-source-info').on('click', (event) => {
            event.preventDefault()
            toggleFlexItems(sourceInfoFlexItems, 'on')
            toggleFlexItems(sourceInfoExpandButton, 'off')
        })
    }

    const transferGroupFlexItems = [
        '#id_grouptransfer-new_group_name',
        '#id_grouptransfer-group_description',
    ]

    var groupDescriptionFlexItems = [
        ...$('[id^=id_groupname-').map(function() { return `[id='${this.id}']` })
    ]

    if (transferGroupFlexItems.some((selector) => elementExists(selector))) {
        let groupName = $('#id_grouptransfer-group_name').val()
        let currentGroupDescId = `[id='id_groupname-${groupName}']`
        toggleFlexItems(groupDescriptionFlexItems.filter(id => id !== currentGroupDescId), 'off')
        if (elementExists(currentGroupDescId)) {
            toggleFlexItems([currentGroupDescId], 'on')
        }
        let state = groupName.toLowerCase().trim() === 'add new group' ? 'on' : 'off'
        toggleFlexItems(transferGroupFlexItems, state)

        $('#id_grouptransfer-group_name').change(function() {
            let groupName = $(this).val()
            let currentGroupDescId = `[id='id_groupname-${groupName}']`
            toggleFlexItems(groupDescriptionFlexItems.filter(id => id !== currentGroupDescId), 'off')
            if (elementExists(currentGroupDescId)) {
                toggleFlexItems([currentGroupDescId], 'on')
            }
            let state = groupName.toLowerCase().trim() === 'add new group' ? 'on' : 'off'
            toggleFlexItems(transferGroupFlexItems, state)
        })
    }

    const otherProvinceFlexItems = [
        '#id_contactinfo-other_province_or_state',
    ]

    if (otherProvinceFlexItems.some((selector) => elementExists(selector))) {
        let value = $('#id_contactinfo-province_or_state').val().toLowerCase().trim()
        let state = value === 'other' ? 'on' : 'off'
        toggleFlexItems(otherProvinceFlexItems, state)
        $('#id_contactinfo-province_or_state').change(function() {
            let state = $(this).val().toLowerCase().trim() === 'other' ? 'on' : 'off'
            toggleFlexItems(otherProvinceFlexItems, state)
        })
    }
})
