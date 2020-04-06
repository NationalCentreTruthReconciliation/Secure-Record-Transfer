$(function() {
    $('input[id$="phone_number"').each(function() {
        $(this).mask('+0 (000) 000-0000')
    })

    $('input[id$="date_of_material"').each(function() {
        $(this).mask('0000-00-00')
    })
})
