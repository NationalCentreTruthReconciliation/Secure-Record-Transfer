import IMask from 'imask';

$(() => {
    /***************************************************************************
     * jQuery Date Picker Setup
     **************************************************************************/
     // Map original function to _old
    $.datepicker._generateHTML_old = $.datepicker._generateHTML;
    // Override the function.
    $.datepicker._generateHTML = function(inst) {
        var html = this._generateHTML_old(inst);
        var pickerName = ($('#' + inst.id).hasClass("start_date_picker") ? "start_date" : "end_date");
        var checkboxName = pickerName + "_is_approximate_mirror";
        var hiddenName = "id_recorddescription-" + pickerName + "_is_approximate";
        var hiddenChecked = $('#' + hiddenName).is(':checked');
        var appendHtml = [
             '<div style="margin-bottom: 5px;">',
             '    <input id="' + checkboxName + '" type="checkbox"' +
             (hiddenChecked ? ' checked="checked"' : "") + '>',
             '    <label>&nbsp;Date Estimated</label>',
             '</div>',
          ].join('\n');

        setTimeout(function() {
            $('#' + checkboxName).on('click', function(event) {
                checked = $(this).is(':checked')
                $('#' + hiddenName).prop('checked', checked)
            });
        }, 5);
        return html + appendHtml;
    }

    $('.start_date_picker, .end_date_picker').datepicker({
        dateFormat: "yy-mm-dd",
        changeMonth: true,
        changeYear: true,
        minDate: new Date(1700, 1, 1),
        maxDate: 0,
    })

    /***************************************************************************
     * Input Mask Setup
     **************************************************************************/

    document.querySelectorAll('input[id$=phone_number]').forEach((el) => {
        IMask(el, {
            mask: '+0 (000) 000-0000',
        });
    });

    document.querySelectorAll('input[id$=date_of_material]').forEach((el) => {
        IMask(el, {
            mask: '0000-00-00',
        });
    });

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
