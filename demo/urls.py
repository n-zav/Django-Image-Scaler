from django.conf.urls import patterns, url, include
from django.contrib import admin

from demo.views import thumbnail

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^image_scaler/',
                           include('image_scaler.urls')),
                       url(r'^show_thumbnail/(?P<image_id>\d+)/$', thumbnail,
                           name='show-thumbnail'),
)
