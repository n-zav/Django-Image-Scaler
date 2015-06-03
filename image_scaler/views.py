import base64
import logging
from django.core.files.images import get_image_dimensions
import os
import json
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import sys
import requests

from .forms import FileForm

UPLOAD_PATH = getattr(settings, 'AJAXIMAGE_DIR', 'uploads/')
AUTH_TEST = getattr(settings, 'AJAXIMAGE_AUTH_TEST', lambda u: u.is_staff)
FILENAME_NORMALIZER = getattr(settings, 'AJAXIMAGE_FILENAME_NORMALIZER',
                              slugify)
IMAGE_TYPES = getattr(settings, 'AJAXIMAGE_IMAGE_TYPES',
                      ['image/png', 'image/jpg', 'image/jpeg', 'image/pjpeg',
                       'image/gif'])
IMAGE_TYPES_FOR_TINY_PNG = getattr(settings, 'IMAGE_TYPES_FOR_TINY_PNG',
                                   ['image/png', 'image/jpeg'])
logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
@user_passes_test(AUTH_TEST)
def image_ratio_ajax(request, upload_to=None, form_class=FileForm):
    """
    Processes ajax post from imagescaler.
    """
    form = form_class(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = request.FILES['file']
        if uploaded_file.content_type in IMAGE_TYPES:
            file_name, extension = os.path.splitext(uploaded_file.name)
            safe_name = '{0}{1}'.format(FILENAME_NORMALIZER(file_name),
                                        extension)
            name = os.path.join(upload_to or UPLOAD_PATH, safe_name)
            path = default_storage.save(name, uploaded_file)
            full_path = default_storage.path(path)
            try:
                os.chmod(full_path, 0660)
            except Exception:
                print sys.exc_info()
            if settings.TINY_PNG_ENABLED is True and uploaded_file.content_type in \
                    IMAGE_TYPES_FOR_TINY_PNG:
                compress_image(default_storage.path(path))
            size = get_image_dimensions(default_storage.path(path), True)
            if size:
                width, height = size
                return HttpResponse(json.dumps({
                    'url': default_storage.url(path),
                    'filename': path,
                    'data': {'width': width, 'height': height}
                }))
        return HttpResponse(status=403, content='Bad image format')
    return HttpResponse(status=403)


def compress_image(file_path):
    """
    Compresses the image from its full path using TINY PNG api.
    """
    try:
        auth_str = "api:" + settings.TINY_PNG_API_KEY
        result = None

        with open(file_path, "rb") as image:
            response = requests.post(
                settings.TINY_PNG_COMPRESSION_URL,
                headers={'Authorization': "Basic %s" % base64.b64encode(auth_str)},
                data=image
            )
            if response.status_code == 201:
                result = requests.get(response.headers['Location']).content

        with open(file_path, "wb") as image:
            image.write(result)

    except Exception:
        logger.exception("error during compressing using tinypng web service")
