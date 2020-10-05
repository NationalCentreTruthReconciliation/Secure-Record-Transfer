// jQuery UI tooltip
$(() => {
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
