from django.contrib import admin

from demo.models import Image, Slide


class ImageAdmin(admin.ModelAdmin):
    model = Image
admin.site.register(Image, ImageAdmin)


class SlideAdmin(admin.ModelAdmin):
    model = Slide
admin.site.register(Slide, SlideAdmin)
