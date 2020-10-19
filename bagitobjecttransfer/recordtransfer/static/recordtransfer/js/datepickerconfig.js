// After page loads:
$(() => {
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
})
