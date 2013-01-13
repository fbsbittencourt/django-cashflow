$(function(){
	$('.datepicker').datepicker()

    $('#id_period').change(function(){
        dates = $(this).val().split(';')
        $('#id_start_date').val(dates[0])
        $('#id_end_date').val(dates[1])
    })
})
