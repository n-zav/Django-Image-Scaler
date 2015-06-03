from django import template
from django.core.files.storage import default_storage
from django.core.files.images import get_image_dimensions
from easy_thumbnails.files import get_thumbnailer
from django.conf import settings
register = template.Library()


@register.tag
def cropped_thumbnail(parser, token):
    """
    Syntax:
    {% cropped_thumbnail instancename ratiofieldname [
    scale=0.1|width=100|height=200] [upscale] [focal_point|focal_point_as_bg]%}
    """
    args = token.split_contents()

    if len(args) < 2:
        # requites model and ratiofieldname
        raise template.TemplateSyntaxError(
            "%r tag requires at least two arguments" % args[0])

    option = None
    upscale = False
    focal_point = False
    focal_point_as_bg = False

    instance = args[1]
    # strip quotes from ratio field
    ratiofieldname = args[2].strip('"\'')

    # parse additional arguments
    for arg in args[3:]:
        arg = arg.lower()
        try:
            name, value = arg.split('=')

            if option:
                raise template.TemplateSyntaxError(
                    "%s: there is already an option defined!" % arg)
            try:  # parse option
                try:
                    option = (name, float(value))
                except ValueError:
                    if name != 'max_size':
                        raise
                    if not 'x' in value:
                        raise template.TemplateSyntaxError(
                            "%s must match INTxINT" % args[3])
                    option = (name, list(map(int, value.split('x'))))
                else:
                    if not option[0] in ('scale', 'width', 'height'):
                        raise template.TemplateSyntaxError(
                            "invalid optional argument %s" % args[3])
                    if option[1] < 0:
                        raise template.TemplateSyntaxError(
                            "%s must have a positive value" % option[0])
            except ValueError:
                raise template.TemplateSyntaxError(
                    "%s needs an numeric argument" % args[3])

        except ValueError:
            if arg == 'upscale':
                upscale = True
            else:
                if arg == 'focal_point':
                    focal_point = True
                elif arg == 'focal_point_as_bg':
                    focal_point_as_bg = True
                else:
                    raise template.TemplateSyntaxError(
                        "%s is an invalid option" % arg)
    return CroppingNode(instance, ratiofieldname, option, upscale, focal_point,
                        focal_point_as_bg)


class CroppingNode(template.Node):
    MAX_SIZE = 150
    FOCAL_POINT_TEMPLATE \
        = '<div class="focal-point %s"><div><img src="%s" alt=""/></div></div>'
    NO_FOCAL_POINT_TEMPLATE = '<img src="%s" />'
    FOCAL_POINT_AS_BG_TEMPLATE = """
    <div style="background-image: url({background_image});
                background-size: cover;
                background-position: {left_right_percentage}%
                                     {top_bottom_percentage}%;
                height: 100%">
    </div>
     """

    def __init__(self, instance, ratiofieldname, option=None, upscale=False,
                 focal_point=False, focal_point_as_bg=False):
        self.instance = instance
        self.ratiofieldname = ratiofieldname
        self.option = option
        self.upscale = upscale
        self.focal_point = focal_point
        self.focal_point_as_bg = focal_point_as_bg

    def render(self, context):
        instance = template.Variable(self.instance).resolve(context)
        if not instance:
            return
        ratiofield = instance._meta.get_field(self.ratiofieldname)
        value = getattr(instance, self.ratiofieldname)
        output = ''
        if value:
            slides = value.split(':|:')
            for slide in slides:
                values = slide.split(":")
                if len(values) == 6:
                    image_file = values[0]
                    box = [self._make_integer(v) for v in values[1:5]]
                    focal_point = self._make_integer(values[-1])
                    image_src = settings.MEDIA_URL + image_file
                    thumbnail = ''
                    size = self._get_size(image_file, ratiofield)
                    if size:
                        thumbnail = self.create_thumbnail(box, image_file, size)

                    # if focal point is not selected and cropping is disabled
                    if focal_point == -2:
                        output += self.NO_FOCAL_POINT_TEMPLATE % (image_src,)
                    # if focal point is not selected and cropping is enabled
                    elif focal_point == -1:
                        output += self.NO_FOCAL_POINT_TEMPLATE % (thumbnail.url,)
                    else:
                        if self.focal_point:
                            css_classes = self._get_css_classes(thumbnail.width,
                                                                thumbnail.height,
                                                                focal_point)
                            if css_classes:
                                output += self.FOCAL_POINT_TEMPLATE % (
                                    css_classes,
                                    thumbnail.url)
                        elif self.focal_point_as_bg:
                            bg_options = \
                                self._get_background_options(focal_point)
                            if bg_options:
                                output += \
                                    self.FOCAL_POINT_AS_BG_TEMPLATE.format(
                                        background_image=thumbnail.url,
                                        left_right_percentage=bg_options[0],
                                        top_bottom_percentage=bg_options[1]
                                    )
                        else:
                            output += self.NO_FOCAL_POINT_TEMPLATE % (
                                thumbnail.url,)
        return output

    def create_thumbnail(self, box, image_file, size):
        """
        creates thumbnail from image file according to box values
        """
        thumbnailer = get_thumbnailer(image_file)
        thumbnail_options = {
            'size': size,
            'box': box,
            'crop': True,
            'detail': True,
            'upscale': self.upscale,
        }
        thumbnail = thumbnailer.get_thumbnail(thumbnail_options)
        return thumbnail

    def _get_css_classes(self, width, height, n):
        """
        takes value of the cell from 0 to 143 and transforms it into a class name,
        by getting coordinates of the cell in a grid 12x12
        n = [int]
        """
        if width < self.MAX_SIZE or height < self.MAX_SIZE:
            return ''

        class_name_list = []
        coordinate_i = n // 12 - 6
        if coordinate_i < 0:
            class_name_list.append('up' + str(coordinate_i))
        elif coordinate_i > 0:
            class_name_list.append('down-' + str(coordinate_i + 1))
        else:
            class_name_list.append('down-1')

        coordinate_j = n % 12 - 6
        if coordinate_j > 0:
            class_name_list.append('right-' + str(coordinate_j + 1))
        elif coordinate_j < 0:
            class_name_list.append('left' + str(coordinate_j))
        else:
            class_name_list.append('right-1')

        class_names = ''
        if len(class_name_list) > 1:
            class_names = ' '.join(class_name_list)

        return class_names

    def _get_background_options(self, n):
        """
        takes value of the cell from 0 to 143 and transforms it into
        background position percentage
        n = [int]
        """
        row = n // 12 + 1
        column = n % 12 + 1
        top_bottom_percentage = row * 100 / 12
        left_right_percentage = column * 100 / 12

        return left_right_percentage, top_bottom_percentage

    def _get_size(self, image_file, ratiofield):
        ratio = ratiofield.ratio_width / float(ratiofield.ratio_height)
        try:
            width, height = get_image_dimensions(default_storage.path(image_file), True)

            size = (height * ratio, height)
            option = self.option

            if option:
                if option[0] == 'scale':
                    width = size[0] * option[1]
                    height = size[1] * option[1]
                elif option[0] == 'width':
                    width = option[1]
                    height = size[1] * width / size[0]
                elif option[0] == 'height':
                    height = option[1]
                    width = height * size[0] / size[1]
                elif option[0] == 'max_size':
                    max_width, max_height = option[1]
                    width, height = size
                    # recalculate height if needed
                    if max_width < width:
                        height = height * max_width / width
                        width = max_width
                    # recalculate width if needed
                    if max_height < height:
                        width = max_height * width / height
                        height = max_height

                size = (width, height)
            return size
        except IOError:
            print "image %s does not exist" % image_file
            return None

    @staticmethod
    def _make_integer(s):
        s = s.strip()
        return int(s) if s else 0

@register.simple_tag
def load_focal_point_css():
    html = "<link rel=" + '"stylesheet"' + "href='" + settings.STATIC_URL +\
           "image_scaler/css/focal-point.css'" + ">"

    return html
