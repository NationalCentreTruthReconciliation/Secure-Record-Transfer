$(() => {
    /***************************************************************************
     * jQuery Date Picker Setup
     **************************************************************************/
    $('.start_date_picker').datepicker({
        dateFormat: "yy-mm-dd",
        minDate: new Date(1700, 1, 1),
        maxDate: 0,
    })

    $('.end_date_picker').datepicker({
        dateFormat:"yy-mm-dd",
        minDate: new Date(1700, 1, 1),
        maxDate: 0,
    })

    /***************************************************************************
     * jQuery Input Mask Setup
     **************************************************************************/
    $('input[id$="phone_number"').each(function() {
        $(this).mask('+0 (000) 000-0000')
    })

    $('input[id$="date_of_material"').each(function() {
        $(this).mask('0000-00-00')
    })

    /***************************************************************************
     * jQuery UI Tooltip Setup
     **************************************************************************/
    $('.help-tooltip').tooltip({
        items: 'div[tooltip-content]',
        content: function() {
            return $(this).attr('tooltip-content')
        },
        position: {
            my: 'right-5',
            at: 'left',
        },
        tooltipClass: 'form-tooltip',
    })
})
