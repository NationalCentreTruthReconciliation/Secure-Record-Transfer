// JavaScript code adapted from this article:
// https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0

const VALID_INPUTS = 'input:not([type=button]):not([type=submit]):not([type=reset]), textarea'
const ID_NUM_REGEX = new RegExp('-(\\d+)-')

function appendNewForm(cloneFormSelector, prefix) {
    var totalForms = parseInt($(`#id_${prefix}-TOTAL_FORMS`).val())
    var maxNumForms = parseInt($(`#id_${prefix}-MAX_NUM_FORMS`).val())

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

function deleteForm(deleteFormSelector, prefix) {
    var total = parseInt($(`#id_${prefix}-TOTAL_FORMS`).val())

    if (total > 1) {
        $(deleteFormSelector).remove()

        var forms = $('.form-row')
        $(`#id_${prefix}-TOTAL_FORMS`).val(forms.length)

        // Update each input's index for the remaining forms
        for (var i = 0; i < forms.length; i++) {
            $(forms.get(i)).find(':input').each((_, element) => {
                updateElementIndex(element, prefix, i);
            });
        }
    }
}

function updateElementIndex(element, prefix, index) {
    var id_regex = new RegExp(`(${prefix}-\\d+)`);
    var replacement = prefix + '-' + index;

    forValue = $(element).attr("for")
    if (forValue) {
        const new_for = forValue.replace(id_regex, replacement)
        $(element).attr({
            "for": new_for
        })
    }

    if (element.id) {
        element.id = element.id.replace(id_regex, replacement)
    }

    if (element.name) {
        element.name = element.name.replace(id_regex, replacement)
    }
}

function elementExists(selector) {
    return $(selector).length === 0 ? false : true
}

$(() => {
    $('.add-form-row').on('click', (event) => {
        event.preventDefault()
        $('.remove-form-row').prop('disabled', false)
        if (elementExists('#id_rights-TOTAL_FORMS')) {
            appendNewForm('.form-row:last', 'rights')
        }
        else if (elementExists('#id_otheridentifiers-TOTAL_FORMS')) {
            appendNewForm('.form-row:last', 'otheridentifiers')
        }
    })

    $('.remove-form-row').on('click', (event) => {
        event.preventDefault()

        if (elementExists('#id_rights-TOTAL_FORMS')) {
            deleteForm('.form-row:last', 'rights')
            total = parseInt($('#id_rights-TOTAL_FORMS').val())
            if (total <= 1) {
                $('.remove-form-row').prop('disabled', true)
            }
        }
        else if (elementExists('#id_otheridentifiers-TOTAL_FORMS')) {
            deleteForm('.form-row:last', 'otheridentifiers')
            total = parseInt($('#id_otheridentifiers-TOTAL_FORMS').val())
            if (total <= 1) {
                $('.remove-form-row').prop('disabled', true)
            }
        }
    })

    $('.remove-form-row').hover(() => {
        var total = 0
        if (elementExists('#id_rights-TOTAL_FORMS')) {
            total = parseInt($('#id_rights-TOTAL_FORMS').val())
        }
        else if (elementExists('#id_otheridentifiers-TOTAL_FORMS')) {
            total = parseInt($('#id_otheridentifiers-TOTAL_FORMS').val())
        }
        if (total > 1) {
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
