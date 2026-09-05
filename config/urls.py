from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.sitemaps import CategoryCommuneSitemap, CommunitySitemap, ProviderSitemap, StaticViewSitemap
from core.views import robots_txt

SITEMAPS = {
    'static': StaticViewSitemap,
    'providers': ProviderSitemap,
    'comunas': CommunitySitemap,
    'categoria_comuna': CategoryCommuneSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('', include('core.urls')),
    path('', include('directory.urls')),
    path('', include('accounts.urls')),
]

# El admin solo existe si ADMIN_URL está definido (en producción va en una ruta secreta).
if settings.ADMIN_ENABLED:
    urlpatterns.insert(0, path(settings.ADMIN_URL, admin.site.urls))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
