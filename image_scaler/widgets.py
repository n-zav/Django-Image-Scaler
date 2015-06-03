from __future__ import unicode_literals
from django.core.files.images import get_image_dimensions
import logging
import os
logger = logging.getLogger(__name__)

from django.conf import settings
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from easy_thumbnails.files import get_thumbnailer

SlideRatioCropWidget_NewTemplate_HTML = """
<div>
    {gallery_output}

    <div id="{name}_template_wrapper" style="display:none">
        {gallery_new_element_template}
    </div>
</div>
"""

button_HTML = """
<div class="space-clear"></div>
<button  id="{name}_add_image" type="button">Add image</button>

<script type="text/javascript">
    var add_new_image = function ($) {{
        function init() {{
            var {name}elementIdPrefix = {last_index};
            var {name}lastIndex = {last_index};
            $('#{name}_add_image').click(function () {{
                var newItemHtml = $('#{name}_template_wrapper').html();
                newItemHtml = newItemHtml.replace(new RegExp('{{new_element_index}}', 'g'), {name}lastIndex);
                $('#{name}_gallery_container').append(newItemHtml);
                {name}lastIndex++;
            }});
        }}
        return {{init: init}};
    }}(django.jQuery);

    django.jQuery.noConflict(true)(function () {{
        add_new_image.init();
    }});
</script>
"""

SlideRatioUploadChoice_HTML = """
<br style="clear:both"/>
<br style="clear:both"/>
<div class="radio_wrapper" id="{name}_{element_id}_{element_index}">
    <div class='radio_widget'>
        <ul id="radio_widget_{element_id}_{element_index}:">
            <li><label for="{element_id}_{element_index}_0">
                <input id="{element_id}_{element_index}_0" name="{name}_radio"
                type="radio" value="server" /> Datei auf Server ausw&auml;hlen</label>
            </li>
            <li><label for="{element_id}_{element_index}_1">
                <input id="{element_id}_{element_index}_1" name="{name}_radio"
                type="radio" value="upload" /> Neues Bild hochladen</label>
            </li>
        </ul>
    </div>
    <div class='server_upload' style='display:none'>
        <ul class='image_ul'>{thumbnail_uploads_list}</ul>
        <div class='image_ul_clear'></div>
    </div>
    <div class='browse_upload' style='display:none' >
        <div id="{element_id}_{element_index}" class="ajaximage" data-url="{upload_url}">
            <label for="{name}_enabled">Zuschneiden aktivieren</label>
            <input type="checkbox" class="image-ratio-enabled"
                name="{name}_enabled"
                data-element-id="{name}_{element_id}_{element_index}"/>
            <a class="remove" href="#remove">Remove</a>
            <br style="clear:both" />
            <input type="hidden" class="image-ratio"
                value="{value}" name="{name}[]"
                data-org-width="{org_width}" data-org-height="{org_height}"
                data-ratio="{ratio}"
                data-min-width="{min_width}" data-min-height="{min_height}"
                data-size-warning="{size_warning}"
                data-filename="{filename}"
            data-thumbnail-url="{file_url}"/>

            <input type="file" class="fileinput" />
            <div class="progress progress-striped active">
                <div class="bar"></div>
            </div>
            <div class="jcrop-holder"></div>
            <div class="image-preview-container"
                class="jcrop-holder image_preview_container"></div>
            <div class="jcrop-holder-warning">Bild zu klein.
            Mindestgr&ouml;&szlig;e des Bildes {min_width}x{min_height}</div>
            <div class="jcrop-holder-image"></div>
        </div>
    </div>
</div>
<br style="clear:both"/>
"""

ServerUploadThumbnail_HTML = """
<li class="image_select"
    data-url="%s"
    data-filename="%s"
    data-width="%s"
    data-height="%s"
    style="list-style: none">
    <img src=%s />
</li>
"""


class SlideRatioCropWidget(widgets.TextInput):

    class Media:
        js = (
            'shared-bg/js/jquery.iframe-transport.js',
            'shared-bg/js/jquery.ui.widget.js',
            'shared-bg/js/jquery.fileupload.js',
            'image_scaler/js/ajaximage.js',
            "image_scaler/js/jquery.Jcrop.min.js",
            "image_scaler/js/image_scale_preview.js",
            "image_scaler/js/jquery.quick.pagination.min.js",
            "image_scaler/js/quickpager.jquery.js",
            "image_scaler/js/radiobutton.js",
        )
        css = {'all': (
            'shared-bg/css/bootstrap-progress.min.css',
            "image_scaler/css/jquery.Jcrop.min.css",
            'image_scaler/css/styles.css',
        )}

    def __init__(self, upload_to, ratio, min_width, min_height,
                 size_warning, is_multiple=True, *args, **kwargs):
        self.upload_to = upload_to
        self.ratio = ratio
        self.min_width = min_width
        self.min_height = min_height
        self.size_warning = size_warning
        self.is_multiple = is_multiple
        super(SlideRatioCropWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        thumbnail_uploads_list = self._get_thumbnail_uploads_list()
        upload_url = reverse('ajaximage', kwargs={'upload_to': self.upload_to})
        element_id = self.build_attrs(attrs).get('id')
        slides = self.decompress(value)

        if self.is_multiple:
            gallery_output = self._get_multiple(name, slides, element_id, thumbnail_uploads_list)
            new_gallery_item = self._get_new_item(upload_url, element_id, name,
                                                  thumbnail_uploads_list)
            output = SlideRatioCropWidget_NewTemplate_HTML.format(
                gallery_output=gallery_output,
                gallery_new_element_template=new_gallery_item,
                name=name)
        else:
            gallery_output = self._get_single(value, name, upload_url, element_id,
                                              thumbnail_uploads_list)
            output = SlideRatioCropWidget_NewTemplate_HTML.format(
                gallery_output=gallery_output,
                gallery_new_element_template='',
                name=name)
        return mark_safe(unicode(output))

    def _get_single(self, value, name, upload_url, element_id, thumbnail_uploads_list):
        """
        Get output for one image.
        """
        value = self.decompress(value)
        file_url = ''
        width = ''
        height = ''
        file_path= ''
        gallery_output = \
            '<div id="' + name + '_gallery_container" class="gallery_container">'
        if value:
            file_path = self._get_file_path(value[0])
            if file_path:
                file_url = default_storage.url(file_path)
                try:
                    width, height = get_image_dimensions(
                        default_storage.path(file_path), True)

                except IOError:
                    print("File does not exist")
        gallery_output += SlideRatioUploadChoice_HTML.format(
            upload_url=upload_url,
            filename=file_path,
            file_url=file_url,
            value=value,
            element_id=element_id,
            element_index=1,
            org_width=width,
            org_height=height,
            ratio=self.ratio,
            min_width=self.min_width,
            min_height=self.min_height,
            size_warning=self.size_warning,
            name=name,
            thumbnail_uploads_list=thumbnail_uploads_list)

        gallery_output += '</div>'
        return gallery_output

    def _get_multiple(self, name, slides, element_id, thumbnail_uploads_list):
        """
        Get output for several images.
        """
        file_url = ''
        width = ''
        height = ''
        gallery_output = \
            '<div id="' + name + '_gallery_container" class="gallery_container">'
        for slide in slides:
            element_index = str(slides.index(slide))
            file_path = self._get_file_path(slide)
            if file_path:
                file_url = default_storage.url(file_path)
                try:
                    width, height = get_image_dimensions(
                        default_storage.path(file_path), True)
                except IOError:
                    print("File does not exist")
            gallery_output += SlideRatioUploadChoice_HTML.format(
                upload_url=reverse('ajaximage', kwargs={'upload_to': self.upload_to}),
                filename=file_path,
                file_url=file_url,
                value=slides[int(element_index)],
                element_id=element_id,
                element_index=element_index,
                org_width=width,
                org_height=height,
                ratio=self.ratio,
                min_width=self.min_width,
                min_height=self.min_height,
                size_warning=self.size_warning,
                name=name,
                thumbnail_uploads_list=thumbnail_uploads_list)
            gallery_output += '</div>'
            gallery_output += button_HTML.format(
                name=name,
                element_id=element_id,
                last_index=str(len(slides)))
        return gallery_output

    def _get_new_item(self, upload_url, element_id, name, thumbnail_uploads_list):
        """
        Get output for adding a new item.
        """
        return SlideRatioUploadChoice_HTML.format(
            upload_url=upload_url,
            filename="",
            file_url="",
            value="",
            element_id=element_id,
            element_index='{new_element_index}',
            org_width="",
            org_height="",
            ratio=self.ratio,
            min_width=self.min_width,
            min_height=self.min_height,
            size_warning=self.size_warning,
            name=name,
            thumbnail_uploads_list=thumbnail_uploads_list)

    def decompress(self, value):
        if value:
            return value.split(':|:')
        else:
            return []

    def value_from_datadict(self, data, files, name):
        slides_list = []
        for value in data.getlist(name + '[]'):
            if len(value.split(':')) == 6:
                slides_list.append(value)
        return ':|:'.join(slides_list)

    def _get_file_path(self, slide):
        """
        parses file path from a string like this:
        u'uploads/9690660-r3l8t8d-900-1.png:92:76:559:387:97'
        """
        file_path = ''
        value_parts = slide.split(':')
        if len(value_parts) == 6:
            file_path = value_parts[0]
        return file_path

    def _get_thumbnail_uploads_list(self):
        """
        gets or creates thumbnails for images in "uploads" folder on the server
        """
        uploads_list = os.listdir(settings.MEDIA_ROOT + '/uploads')
        thumbnail_uploads_list = ''
        for item in uploads_list:
            if item.endswith(('.jpg', '.png', '.jpeg', '.pjpeg', '.gif')):
                try:
                    picture = open(settings.MEDIA_ROOT + '/uploads/' + item)
                    picture_url = settings.MEDIA_URL + 'uploads/' + item
                    picture_filename = 'uploads/' + item
                    size = get_image_dimensions(picture)
                    relative_name = 'uploads/thumbnails/' + item
                    thumbnailer = get_thumbnailer(picture,
                                                  relative_name=relative_name)
                    thumbnail = thumbnailer.get_thumbnail({'size': (100, 100),
                                                           'crop': True})
                    thumbnail_uploads_list += ServerUploadThumbnail_HTML % (
                        picture_url,
                        picture_filename,
                        size[0],  # width
                        size[1],  # height
                        thumbnail.url)
                except ValueError:
                    continue
            else:
                continue
        return thumbnail_uploads_list
