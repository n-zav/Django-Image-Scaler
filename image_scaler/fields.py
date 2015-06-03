from __future__ import unicode_literals
from django.core.files.storage import default_storage
from django.db import models
from django.conf import settings
from django.db.models.fields.files import FieldFile
from .widgets import SlideRatioCropWidget


class SlideRatioField(models.TextField):
    """
    SlideRatioField  allows to add multiple images as one instance.
    """
    storage = default_storage
    attr_class = FieldFile

    def __init__(self, upload_to, ratio='1x1', verbose_name=None,
                 help_text=None, min_size='0x0',
                 size_warning=getattr(settings, 'IMAGE_SIZE_WARNING', False)):
        self.upload_to = upload_to
        self.ratio_width, self.ratio_height = list(map(int, ratio.split('x')))
        self.min_width, self.min_height = list(map(int, min_size.split('x')))
        self.size_warning = size_warning
        field_kwargs = {
            'max_length': 255,
            'blank': True,
            'verbose_name': verbose_name,
            'help_text': help_text,
        }
        super(SlideRatioField, self).__init__(**field_kwargs)

    def deconstruct(self):
        """
        Needed for Django 1.7+ migrations. Generate args and kwargs from current
        field values.
        """
        kwargs = {
            'verbose_name': self.verbose_name,
            'help_text': self.help_text,
            'size_warning': self.size_warning,
            'upload_to': self.upload_to
        }
        return self.name, 'image_scaler.fields.SlideRatioField', (), kwargs

    def contribute_to_class(self, cls, name, virtual_only=False):
        super(SlideRatioField, self).contribute_to_class(cls, name)

    def get_prep_value(self, value):
        """Returns field's value prepared for saving into a database."""
        # Need to convert File objects provided via a form to unicode for
        # database insertion
        if value is None:
            return None
        return str(value)

    def get_internal_type(self):
        return "TextField"

    def formfield(self, **kwargs):
        ratio = self.ratio_width / float(self.ratio_height)
        kwargs['widget'] = \
            SlideRatioCropWidget(self.upload_to,
                                 ratio,
                                 self.min_width,
                                 self.min_height,
                                 str(self.size_warning).lower())
        return super(SlideRatioField, self).formfield(**kwargs)

    def south_field_triple(self):
        """
        Return a suitable description of this field for South.
        """
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector

        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class ImageRatioField(SlideRatioField):
    """
    ImageRatioField allows to add only one image.
    """
    def formfield(self, **kwargs):
        ratio = self.ratio_width / float(self.ratio_height)
        kwargs['widget'] = \
            SlideRatioCropWidget(self.upload_to,
                                 ratio,
                                 self.min_width,
                                 self.min_height,
                                 str(self.size_warning).lower(),
                                 False)
        return super(SlideRatioField, self).formfield(**kwargs)
