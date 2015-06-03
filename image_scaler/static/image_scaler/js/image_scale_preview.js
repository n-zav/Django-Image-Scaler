var image_cropping = function ($) {
    var MAX_SIZE = 150;

    function init() {
        $('div.gallery_container input.image-ratio').each(function () {
            var $this = $(this);
            var values = $this.val().replace('[', '').replace(']', '');
            if ($this.attr('data-thumbnail-url')) {
                if (values.length > 0) {
                    var initial = _parse_field_value(values);
                    if (initial[5] != -2) {
                        $(this).siblings('.image-ratio-enabled').prop('checked', true);
                        init_input($this);
                    } else {
                        init_input_readonly($this);
                    }
                }
            }
        });
        $('div.gallery_container').on('change', 'input.image-ratio-enabled', function () {
            var $element = $('#' + $(this).data('element-id'));
            var $input = $element.find('input.image-ratio');
            if ($input.attr('data-thumbnail-url')) {
                reset_input($input);
                if (this.checked) {
                    init_input($input);
                } else {
                    init_input_readonly($input);
                }
            }
        });
    }

    function init_input_readonly($image_input) {
        var $parent_wrapper = $image_input.parents('.ajaximage');
        var input_id = $parent_wrapper.attr('id'),
            image_id = input_id + '-image',
            org_width = $image_input.attr('data-org-width'),
            org_height = $image_input.attr('data-org-height'),
            min_cropping_width = $image_input.attr('data-min-width'),
            min_cropping_height = $image_input.attr('data-min-height'),
            thumbnail_url = $image_input.attr('data-thumbnail-url'),
            filename = $image_input.attr('data-filename');

        if (org_width - min_cropping_width > 0 && org_height - min_cropping_height > 0) {
            $parent_wrapper.siblings('.jcrop-holder-warning').hide();
            $parent_wrapper.siblings('.jcrop-holder-image').empty();
            var $image = $('<img>', {
                'id': image_id,
                'src': thumbnail_url
            });

            $parent_wrapper.find('.jcrop-holder').append($image);
        } else {
            $('input.image-ratio-enabled').change(function () {
                 if (this.checked) {
                     $parent_wrapper.children('.jcrop-holder-warning').show();
                 }
            });
            var $small_preview_image = $parent_wrapper.children('.jcrop-holder-image');
            $small_preview_image.empty().append('<img class='+ "small_image_preview" + '" src="' + thumbnail_url + '"/>');
        }
        var values = [filename, 10, 10, 10, 10, -2];
        _update_field_value($image_input, values);
    }

    function init_input($image_input) {
        var $parent_wrapper = $image_input.parents('.ajaximage');
        var input_id = $parent_wrapper.attr('id'),
            image_id = input_id + '-image',
            org_width = $image_input.attr('data-org-width'),
            org_height = $image_input.attr('data-org-height'),
            min_cropping_width = $image_input.attr('data-min-width'),
            min_cropping_height = $image_input.attr('data-min-height'),
            ratio = $image_input.attr('data-ratio'),
            preview_height = 200,
            preview_width = preview_height * ratio,
            preview_id = 'preview-' + image_id,
            thumbnail_url = $image_input.attr('data-thumbnail-url');

        if (org_width - min_cropping_width > 0 && org_height - min_cropping_height > 0) {
            $parent_wrapper.children('.jcrop-holder-warning').hide();
            $parent_wrapper.children('.jcrop-holder-image').empty();
            var $image = $('<img>', {
                'id': image_id,
                'src': $image_input.attr('data-thumbnail-url')
            });

            var options = {
                minSize: [min_cropping_width, min_cropping_height],
                keySupport: false,
                trueSize: [org_width, org_height],
                onChange: showPreview(preview_id, org_width, org_height, preview_width, preview_height),
                onSelect: update_selection($image_input),
                addClass: 'jcrop-image'
            };
            if ($image_input.attr('data-ratio')) {
                options['aspectRatio'] = $image_input.attr('data-ratio');
            }

            if ($image_input.val()[0] == "-") {
                // disable cropping
                $image_input.val($image_input.val().substr(1));
            }
            // is the image bigger than the minimal cropping values?
            // otherwise lock cropping area on full image
            var initial;
            var parse_value;
            if ($image_input.val().length > 2) {
                var value_list = $image_input.val().split(':|:');
                $.each(value_list, function(index, value ) {
                    if (value.indexOf(thumbnail_url.slice(7)) >= 0) {
                        parse_value = value;
                        initial = _parse_field_value(parse_value);
                    }
                });
            } else {
                initial = max_cropping(preview_width, preview_height, org_width, org_height);
                initial.unshift($image_input.attr('data-filename'));

                // set cropfield to initial value
                initial[5] = -1;
                _update_field_value($image_input, initial);
            }

            var initial_sel = initial.slice(1, 5);
            $.extend(options, {setSelect: initial_sel});

            $parent_wrapper.children('.jcrop-holder').append($image);

            $('#' + image_id).Jcrop(options, function() {
                var $preview_container = $parent_wrapper.children('.image-preview-container');
                var $preview = $('<div class="img_preview"' + 'style="width:' + preview_width + 'px;' +
                    'height:' + preview_height + 'px;' + 'overflow:hidden;">' +
                    '<img id="' + preview_id + '" src="' + $image_input.attr('data-thumbnail-url') +
                    '"/></div>');
                var $grid = $(_generate_grid_html(preview_width, preview_height));
                $grid.appendTo($preview);
                var focal_point_label_id = 'choose_focal_point' + '_' + image_id;
                var $focal_point_label = '<label style="padding-bottom: 10px;" id=' + focal_point_label_id + '>Focal point:</label>';
                if (min_cropping_width - MAX_SIZE >= 0 && min_cropping_height - MAX_SIZE >= 0) {
                    $($focal_point_label).appendTo($preview_container);
                    $preview.appendTo($preview_container);
                    $grid.find('td').click(function () {
                        var $grid = $(this).parents('table');
                        _select_grid_cell($image_input, $grid, $(this).data("number"));
                    });
                    _select_grid_cell($image_input, $grid, initial[5]);
                    _showPreview($('#' + image_id).data('Jcrop').tellSelect(),
                        preview_id, org_width, org_height, preview_width, preview_height
                    );
                }
            });
        } else {
            $parent_wrapper.children('.jcrop-holder-warning').show();
            var $small_preview_image = $parent_wrapper.children('.jcrop-holder-image');
            $small_preview_image.empty().append('<img class='+ "small_image_preview" + '" src="' + $image_input.attr('data-thumbnail-url') + '"/>');
        }
    }

    function reset_input($image_input) {
        var $parent_wrapper = $image_input.parents('.ajaximage');
        var input_id = $parent_wrapper.attr('id');
        var $image = $parent_wrapper.find('img#' + input_id + '-image');
        var $preview_container = $parent_wrapper.children('.image-preview-container');
        var $small_image_preview = $parent_wrapper.children('.jcrop-holder-image');
        var $size_image_warning = $parent_wrapper.children('.jcrop-holder-warning');

        $image_input.val('');
        var $jCrop = $image.data('Jcrop');
        if ($jCrop) {
            $jCrop.destroy();
        }
        $image.remove();
        $preview_container.empty();
        $small_image_preview.empty();
        $size_image_warning.hide();
    }

    function showPreview(preview_id, org_width, org_height, min_width, min_height) {
        return function (sel) {
            _showPreview(sel, preview_id, org_width, org_height, min_width, min_height);
        };
    }

    function _showPreview(coords, preview_id, org_width, org_height, min_width, min_height) {
        var rx = min_width / coords.w;
        var ry = min_height / coords.h;

        $('#' + preview_id).css({
            width: Math.round(rx * org_width) + 'px',
            height: Math.round(ry * org_height) + 'px',
            marginLeft: '-' + Math.round(rx * coords.x) + 'px',
            marginTop: '-' + Math.round(ry * coords.y) + 'px'
        });
    }

    function max_cropping(width, height, image_width, image_height) {
        var ratio = width / height;
        var offset;

        if (image_width < image_height * ratio) {
            // width fits fully, height needs to be cropped
            offset = Math.round((image_height - (image_width / ratio)) / 2);
            return [0, offset, image_width, image_height - offset, 0];
        }
        // height fits fully, width needs to be cropped
        offset = Math.round((image_width - (image_height * ratio)) / 2);
        return [offset, 0, image_width - offset, image_height, 0];
    }

    function _parse_field_value(val) {
        if (val === '') {
            return
        }
        var s = val.split(':');
        var focal_point = 0;
        if (s[5].length > 0) {
            focal_point = s[5].replace("'",'');
        } else {
            focal_point = -1
        }
        return [
            s[0],
            parseInt(s[1], 10),
            parseInt(s[2], 10),
            parseInt(s[3], 10),
            parseInt(s[4], 10),
            parseInt(focal_point)
        ];
    }

    function _update_selection(sel, $image_input) {
        if ($image_input.attr('data-size-warning')) {
            crop_indication(sel, $image_input);
        }
        var values = [
            $image_input.attr('data-filename'),
            Math.round(sel.x),
            Math.round(sel.y),
            Math.round(sel.x2),
            Math.round(sel.y2),
            $image_input.attr('data-focal-point')
        ];

        _update_field_value($image_input, values);
    }

    function update_selection($image_input) {
        return function (sel) {
            _update_selection(sel, $image_input);
            showPreview(sel);
        };
    }

    function crop_indication(sel, $image_input) {
        // indicate if cropped area gets smaller than the specified minimal cropping
        var $parent_wrapper = $image_input.parents('.ajaximage');
        var $jcrop_holder = $parent_wrapper.children('.jcrop-holder');
        var min_width = $image_input.data("min-width");
        var min_height = $image_input.data("min-height");
        if (min_width > 0 && min_height > 0) {
            if ((sel.w < min_width) || (sel.h < min_height)) {
                $jcrop_holder.addClass('size-warning');
            } else {
                $jcrop_holder.removeClass('size-warning');
            }
        }
    }

    function _generate_grid_html(width, height) {
        var html = '<table class="focal_point_selector" style=' +
            "width:" + width + "px;" + "height:" + height + "px;" +
            'cellspacing="0" cellpadding="0"><tbody>';
        for (var i = 0; i < 12; i++) {
            html += '<tr>';
            for (var j = 0; j < 12; j++){
                html += '<td data-number="' + (i * 12 + j) + '">&nbsp;</td>';
            }
            html += '</tr>';
        }

        html = html + '</tbody></table>';

        return html;
    }

    function _select_grid_cell($image_input, $grid, focal_point) {
        $image_input.attr('data-focal-point', focal_point);

        var values = _parse_field_value($image_input.val());
        values[5] = focal_point;
        _update_field_value($image_input, values);

        $grid.find("td").css({"background-color": "", "opacity": ""});
        var $current_cell = $grid.find('td[data-number="' + focal_point + '"]');
        if ($current_cell.data('selected') == 'selected') {
            $current_cell.css({"background-color": "", "opacity": ""});
            $current_cell.data('selected', '');
        }
        else {
            $current_cell.css({"background-color": "#49fb35", "opacity": 0.4});
            $current_cell.data('selected', 'selected');
        }
    }

    function _update_field_value($image_input, values) {
        $image_input.val(values.join(':'));
    }

    return {
        init: init,
        init_input: init_input,
        init_input_readonly: init_input_readonly,
        reset_input: reset_input
    };
}(django.jQuery);

// init image cropping when DOM is ready
django.jQuery.noConflict(true)(function () {
    image_cropping.init();
});
