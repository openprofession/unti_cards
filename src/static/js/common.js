$(document).ready(function () {

	function setTimer(id, date) {
		$(id).countdown(date).on('update.countdown', function(event) {
			var $this = $(this).html(event.strftime(''
					+ '<div class="timer-block"><span class="timer-block__value">%D</span><span class="timer-block__title">дней</span></div>'
					+ '<div class="timer-block"><span class="timer-block__value">%H</span><span class="timer-block__title">:</span></div>'
					+ '<div class="timer-block"><span class="timer-block__value">%M</span><span class="timer-block__title"></span></div>'
			));
		});
	}

	setTimer('#timer1', '2019/06/30');

	//placeholder
	$('input,textarea').focus(function () {
		$(this).data('placeholder', $(this).attr('placeholder'));
		$(this).attr('placeholder', '');
	});
	$('input,textarea').blur(function () {
		$(this).attr('placeholder', $(this).data('placeholder'));
	});


	function dateSelect(id) {
		$(id).datepicker({
			language: 'ru',
			autoClose: true,
			maxDate: new Date()
		});
	}

	dateSelect('.date-select');


	$('#img').change(function() {
		var input = $(this)[0];
		if (input.files && input.files[0]) {
			if (input.files[0].type.match('image.*')) {
				var reader = new FileReader();
				reader.onload = function(e) {
					$('#img-preview').attr('src', e.target.result);
				}
				reader.readAsDataURL(input.files[0]);
				$('.btn-upload').addClass('active');
				$('.btn-upload').addClass('active');
			} else {
				alert("Этот файл не изображение.");
			}
		} else {
			console.log('Error!');
		}
	});

	/*$('#reset-img-preview').click(function(e) {
		e.preventDefault();
		$('#img').val('');
		$('#img-preview').attr('src', 'img/img-load.png');
		$('#reset-img-preview').hide();
	});*/

	$('.form-setting .collapse').on('show.bs.collapse', function () {
		var text = $(this).closest('.form-setting__row').find('.button-collapse .btn').data('text');
		$(this).closest('.form-setting__row').addClass('collapse-open');
		$(this).closest('.form-setting__row').find('.button-collapse .btn').text(text);
	});

	$('.form-setting .collapse').on('hide.bs.collapse', function () {
		var text2 = $(this).closest('.form-setting__row').find('.button-collapse .btn').data('text2');
		$(this).closest('.form-setting__row').removeClass('collapse-open');
		$(this).closest('.form-setting__row').find('.button-collapse .btn').text(text2);
	});

	$(".custom-file-input").on("change", function() {
		var fileName = $(this).val().split("\\").pop();
		$(this).siblings(".custom-file-label").addClass("selected").html(fileName);
	});

	$('#all1').click(function() {
		if($(this).prop('checked') == true){
			$(this).closest('.form-issue').find('.card-checkbox input[type=checkbox]').prop('checked',true);
		}
		else{
			$(this).closest('.form-issue').find('.card-checkbox input[type=checkbox]').prop('checked',false);
		}
	});

	$('.card-checkbox input[type=checkbox]').click(function() {
		$(this).closest('.form-issue').find('#all1').prop('checked',false);
	});


});



