// JavaScript code adapted from this article:
// https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0

const VALID_INPUTS = 'input:not([type=button]):not([type=submit]):not([type=reset]), textarea'

function appendNewForm(cloneFormSelector, prefix) {
    // TOTAL_FORMS and MAX_NUM_FORMS are 1-based totals
    var totalOne = parseInt($(`#id_${prefix}-TOTAL_FORMS`).val())
    var maxNumForms = parseInt($(`#id_${prefix}-MAX_NUM_FORMS`).val())

    if (totalOne + 1 > maxNumForms) {
        alert(`You may not exceed ${maxNumForms} form sections.`)
        return
    }

    var newForm = $(cloneFormSelector).clone(true)
    newForm.addClass('margin-top-25px')

    // Element IDs are 0-based totals
    var totalZero = totalOne - 1

    oldFormNumber = `-${totalZero}-`
    newFormNumber = `-${totalZero + 1}-`

    $(newForm).find(VALID_INPUTS).each((_, element) => {
        var newName = $(element).attr('name').replace(oldFormNumber, newFormNumber)
        var newId = `id_${newName}`
        $(element).attr({
            'name': newName,
            'id': newId
        })
        .val('')
        .removeAttr('checked')
    })

    $(newForm).find('label').each((_, element) => {
        var forValue = $(element).attr('for')
        if (forValue) {
            var newForValue = forValue.replace(oldFormNumber, newFormNumber)
            $(element).attr({
                'for': newForValue
            })
        }
    })

    $(`#id_${prefix}-TOTAL_FORMS`).val(totalOne + 1);
    $(cloneFormSelector).after(newForm);
}

function deleteLastForm(deleteFormSelector, prefix) {
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

$(() => {
    if ($('#id_rights-TOTAL_FORMS')) {
        $('.add-form-row').on('click', (event) => {
            event.preventDefault()
            appendNewForm('.form-row:last', 'rights')
        })
        $('.remove-form-row').on('click', (event) => {
            event.preventDefault()
            deleteLastForm('.form-row:last', 'rights')
        })
    }
    else if ($('#id_otheridentifiers-TOTAL_FORMS')) {
        $('.add-form-row').on('click', (event) => {
            event.preventDefault()
            appendNewForm('.form-row:last', 'otheridentifiers')
        })
        $('.remove-form-row').on('click', (event) => {
            event.preventDefault()
            deleteLastForm('.form-row:last', 'otheridentifiers')
        })
    }
})