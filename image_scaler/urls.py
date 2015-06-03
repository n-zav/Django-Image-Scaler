try:  # pre 1.6
    from django.conf.urls.defaults import url, patterns
except ImportError:
    from django.conf.urls import url, patterns

from .forms import FileForm

urlpatterns = patterns(
    '',
    url(
        '^ajaximage_upload/(?P<upload_to>.*)/',
        'image_scaler.views.image_ratio_ajax',
        {'form_class': FileForm},
        name='ajaximage'
    ),
)
