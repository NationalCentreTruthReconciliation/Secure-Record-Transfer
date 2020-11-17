/**
 * Functions for adding and removing forms from a formset dynamically. Django does not natively
 * support adding and removing forms from a formset, so it has to be done within JavaScript.
 *
 * Adding new forms is done by cloning a form and appending it after the cloned form.
 *
 * Code loosely adapted from this article:
 * https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
 */


const VALID_INPUTS = 'input:not([type=button]):not([type=submit]):not([type=reset]), textarea'
const ID_NUM_REGEX = new RegExp('-(\\d+)-')


/**
 * Get the current number of forms displayed on the page.
 * @returns {Number} The current number of forms
 */
function getTotalForms() {
    var prefix = getFormPrefix()
    return parseInt($(`#id_${prefix}-TOTAL_FORMS`).val())
}

/**
 * Get the maximum number of allowable forms set by the backend.
 * @returns {Number} The maximum number of forms
 */
function getMaxForms() {
    var prefix = getFormPrefix()
    return parseInt($(`#id_${prefix}-MAX_NUM_FORMS`).val())
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
 * Test if an element exists on the page.
 * @param {String} selector A jQuery type selector string
 * @returns {Boolean} true if element exists, false otherwise
 */
function elementExists(selector) {
    return $(selector).length !== 0
}

/**
 * Add a new form to the formset by cloning the selected form. The cloned form is inserted in the
 * document tree directly below the form that was cloned. This function respects whether the
 * max_num of formsets was set in the backend.
 * @param {String} cloneFormSelector The form to clone to create a new form from
 */
function appendNewForm(cloneFormSelector) {
    var prefix = getFormPrefix()
    var totalForms = getTotalForms()
    var maxNumForms = getMaxForms()

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
    var total = getTotalForms()

    if (total > 1) {
        $(deleteFormSelector).remove()

        var forms = $('.form-row')
        $(`#id_${prefix}-TOTAL_FORMS`).val(forms.length)

        // Update each input's index for the remaining forms
        for (var i = 0; i < forms.length; i++) {
            $(forms.get(i)).find(':input').each((_, element) => {
                updateElementIndex(element, i);
            });
        }
    }
}

/**
 * Update a form element's index within the current form.
 * @param element An element selected from the page with jQuery
 * @param {Number} index The new index the element is to have
 */
function updateElementIndex(element, index) {
    var prefix = getFormPrefix()
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

$(() => {
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
})
