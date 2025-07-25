#from django.contrib import admin
"""from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tools21k.urls')),
    path('video/', include('videodownloader.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""
from django.contrib import admin
from django.urls import path, include,re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('blog/',views.blog,name='blog'),
    path('about/',views.about,name='about'),
    path('help/',views.help,name='help'),
    path('privacypolicy/',views.privacypolicy,name='privacypolicy'),
    path('termsandconditions/',views.termsandconditions,name='termsandconditions'),
    path('',views.home,name='home'),
    path('download/', include('videodownloader.urls')),  # Include app URLs at root
    path('convert/',include('fileconverter.urls')),
    re_path(r'^sitemap\.xml$', serve, {'document_root': settings.STATIC_ROOT, 'path': 'sitemap.xml'}),
    re_path(r'^ads\.txt$', serve, {'document_root': settings.STATIC_ROOT, 'path': 'ads.txt'}),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
