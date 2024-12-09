import IMask from 'imask';
import {
    autoUpdate,
    arrow,
    computePosition,
    flip,
    shift,
    offset,
} from '@floating-ui/dom';


document.addEventListener("DOMContentLoaded", () => {
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
})

// Create tooltips after content positioning is calculated; DOMContentLoaded is too early
window.addEventListener('load', () => {
    document.querySelectorAll('.help-tooltip').forEach((icon) => {
        const tooltip = document.createElement('div');
        tooltip.className = 'form-tooltip';
        tooltip.innerHTML = icon.getAttribute('tooltip-content')

        const arrowElement = document.createElement('div');
        arrowElement.className = 'tooltip-arrow';

        tooltip.appendChild(arrowElement);

        document.body.appendChild(tooltip);

        const cleanup = autoUpdate(icon, tooltip, () => {
            computePosition(icon, tooltip, {
                placement: 'bottom-end',
                middleware: [
                    offset(5),
                    flip(),
                    shift(),
                    arrow({ element: arrowElement }),
                ],
            }).then(({ x, y, placement, middlewareData }) => {
                Object.assign(tooltip.style, {
                    left: `${x}px`,
                    top: `${y}px`,
                });

                // Position the arrow
                const { x: arrowX, y: arrowY } = middlewareData.arrow;

                const staticSide = {
                    top: 'bottom',
                    right: 'left',
                    bottom: 'top',
                    left: 'right',
                }[placement.split('-')[0]];

                Object.assign(arrowElement.style, {
                    left: arrowX != null ? `${arrowX}px` : '',
                    top: arrowY != null ? `${arrowY}px` : '',
                    right: '',
                    bottom: '',
                    [staticSide]: '-4px',
                });
            });
        });

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (Array.from(mutation.removedNodes).includes(icon)) {
                    cleanup();
                    observer.disconnect();
                }
            });
        });

        observer.observe(icon.parentNode, {
            childList: true
        });

        icon.addEventListener('mouseenter', () => {
            tooltip.style.display = 'block';
        });

        icon.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });
    });
});
