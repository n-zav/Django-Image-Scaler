from django.db import models
from image_scaler import SlideRatioField,ImageRatioField


class Image(models.Model):
    image = ImageRatioField('uploads', '3x2', min_size='300x200',
                            size_warning=True, verbose_name='Image field')
    time_added = models.DateTimeField(auto_now=True)


class Slide(models.Model):
    slide = SlideRatioField('teaser_images', '1600x435',
                            min_size='1600x435', size_warning=True)
    time_added = models.DateTimeField(auto_now=True)
