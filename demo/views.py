from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from demo.models import Image, Slide


class IndexTemplateView(TemplateView):
    template_name = "index.html"


def thumbnail(request, image_id):
    """
    shows thumbnail of the image converted in the admin.
    """
    image = get_object_or_404(Image, pk=image_id)
    slider = get_object_or_404(Slide, pk=image_id)

    return render(request, 'thumbnail.html', {'image': image,
                                              'slider': slider})
