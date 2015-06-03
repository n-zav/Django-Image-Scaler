from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from demo.views import IndexTemplateView

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', IndexTemplateView.as_view(), name='home'),
                       url(r'^admin/', include(admin.site.urls)),

                       # image scaler urls
                       (r'^demo/',
                        include('demo.urls')),)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
