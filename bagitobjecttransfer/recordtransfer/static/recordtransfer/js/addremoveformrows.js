function appendNewForm(cloneFormSelector, prefix) {
    var newElement = $(cloneFormSelector).clone(true)

    // TOTAL_FORMS is a 1-based number
    var totalOne = parseInt($(`#id_${prefix}-TOTAL_FORMS`).val())

    // TODO: Check in the future if totalOne + 1 is greater than maximum number of forms allowed

    // Element IDs are 0-based numbers
    var totalZero = totalOne - 1

    oldFormNumber = `-${totalZero}-`
    newFormNumber = `-${totalZero + 1}-`

    validInputs = 'input:not([type=button]):not([type=submit]):not([type=reset])'
    $(newElement).find(validInputs).each((_, element) => {
        var newName = $(element).attr('name').replace(oldFormNumber, newFormNumber)
        var newId = `id_${newName}`
        $(element).attr({
            'name': newName,
            'id': newId
        })
        .val('')
        .removeAttr('checked')
    })

    $(newElement).find('label').each((_, element) => {
        var forValue = $(element).attr('for')
        if (forValue) {
            var newForValue = forValue.replace(oldFormNumber, newFormNumber)
            $(element).attr({
                'for': newForValue
            })
        }
    })

    $(`#id_${prefix}-TOTAL_FORMS`).val(totalOne + 1);
    $(cloneFormSelector).after(newElement);
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