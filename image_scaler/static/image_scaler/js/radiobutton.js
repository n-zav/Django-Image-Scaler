var radio_button = function ($) {
    function init() {
        $('.radio_widget').each(function () {

            init_radio($(this));
        });
    }

    function init_radio($radio_widget) {
        var $parent_wrapper = $radio_widget.parents('.radio_wrapper');
        var $server_upload = $parent_wrapper.find('.server_upload');
        var $browse_upload = $parent_wrapper.find('.browse_upload');
        var $radio_ul = $radio_widget.find('ul');
        $radio_ul.addClass('radio_ul');
        $parent_wrapper.find('.image_ul').quickPagination();
        $radio_widget.find('li').css('list-style', 'none');
        var $currently_checked = $radio_widget.find('input:checked');
        if ($currently_checked.length > 0) {
            if ($currently_checked.val() === 'upload') {
                $server_upload.hide();
                $browse_upload.show();
            } else {
                $server_upload.show();
                $browse_upload.hide();
            }
        } else {
            var $radios = $radio_widget.find('input:radio[value=upload]');

            if ($radios.is(':checked') === false) {
                $radios.filter('[value=upload]').prop('checked', true);
            }
            $server_upload.hide();
            $browse_upload.show();
        }
        $radio_ul.find('input').on('change', function () {
            var $input_image = $parent_wrapper.find('input[class=image-ratio]');
            image_cropping.reset_input($input_image);
            if ($(this).val() === 'upload') {
                $server_upload.hide();
                $browse_upload.show();
                if ($input_image.attr('data-thumbnail-url')) {
                    image_cropping.init_input_readonly($input_image);
                }
            } else {
                $server_upload.show();
                $browse_upload.hide();
            }
        });
       $server_upload.find('li').on("click", function() {
           $(this).css('border', '2px solid #0099CC');
           $(this).siblings().css('border', '0');
           var $image_input = $parent_wrapper.find('input:hidden.image-ratio');
           $image_input.attr('data-thumbnail-url', $(this).data('url'));
           $image_input.attr('data-org-height', $(this).data('height'));
           $image_input.attr('data-filename', $(this).data('filename'));
           $image_input.attr('data-org-width', $(this).data('width'));
           image_cropping.reset_input($image_input);
           image_cropping.init_input_readonly($image_input);
           $browse_upload.show();
       })
    }

        $(document).bind('DOMNodeInserted', function (e) {
        if ($(e.target).hasClass('radio_wrapper')){
            var $radio_widget = $(e.target).find('.radio_widget');
            radio_button.init_radio($radio_widget);
        }
    });

    return {
        init: init,
        init_radio: init_radio
    };
}(django.jQuery);

// init radio button when DOM is ready
django.jQuery.noConflict(true)(function () {

    radio_button.init();

});
