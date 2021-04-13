$(() => {
    /***************************************************************************
     * jQuery Date Picker Setup
     **************************************************************************/
    function addEstimatedButtonToStartDate(instance) {
        var buttonPane = $(instance).datepicker("widget")
        var html = [
            '<div style="margin-bottom: 5px;">',
            '    <input id="start_date_is_approximate_mirror" type="checkbox">',
            '    <label>&nbsp;Date Estimated</label>',
            '</div>',
        ].join('\n')
        buttonPane.append(html)
        if ($('#id_recorddescription-start_date_is_approximate').prop('checked')) {
            $('#start_date_is_approximate_mirror').prop('checked', true)
        }
        $('#start_date_is_approximate_mirror').on('click', function(event) {
            checked = $(this).prop('checked')
            $('#id_recorddescription-start_date_is_approximate').prop('checked', checked)
        })
    }

    function addEstimatedButtonToEndDate(instance) {
        var buttonPane = $(instance).datepicker("widget")
        var html = [
            '<div style="margin-bottom: 5px;">',
            '    <input id="end_date_is_approximate_mirror" type="checkbox">',
            '    <label>&nbsp;Date Estimated</label>',
            '</div>',
        ].join('\n')
        buttonPane.append(html)
        if ($('#id_recorddescription-end_date_is_approximate').prop('checked')) {
            $('#end_date_is_approximate_mirror').prop('checked', true)
        }
        $('#end_date_is_approximate_mirror').on('click', function(event) {
            checked = $(this).prop('checked')
            $('#id_recorddescription-end_date_is_approximate').prop('checked', checked)
        })
    }

    $('.start_date_picker').datepicker({
        dateFormat: "yy-mm-dd",
        changeMonth: true,
        changeYear: true,
        minDate: new Date(1700, 1, 1),
        maxDate: 0,
        beforeShow: function (input, inst) {
            setTimeout(function () {
                addEstimatedButtonToStartDate(input)
            }, 5)
        },
        onChangeMonthYear: function(year, month, inst) {
            setTimeout(function () {
                addEstimatedButtonToStartDate(inst)
            }, 5)
        },
    })

    $('.end_date_picker').datepicker({
        dateFormat:"yy-mm-dd",
        changeMonth: true,
        changeYear: true,
        minDate: new Date(1700, 1, 1),
        maxDate: 0,
        beforeShow: function (input, inst) {
            setTimeout(function () {
                addEstimatedButtonToEndDate(input)
            }, 5)
        },
        onChangeMonthYear: function(year, month, inst) {
            setTimeout(function () {
                addEstimatedButtonToEndDate(inst)
            }, 5)
        },
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
