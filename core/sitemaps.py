from django.contrib.sitemaps import Sitemap
from django.db.models import Count
from django.urls import reverse

from directory.models import Category, Commune, Provider


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['core:home', 'core:join', 'core:about', 'core:trust_and_safety']

    def location(self, item):
        return reverse(item)


class ProviderSitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return Provider.objects.filter(is_active=True).only('slug', 'updated_at').order_by('slug')

    def lastmod(self, obj):
        return obj.updated_at


class CategoryCommuneSitemap(Sitemap):
    """
    Genera una URL por cada combinación (categoría, comuna) con al menos
    1 provider activo. Estas son las landing pages hiperlocales de mayor
    valor SEO: "gasfitero en Maipú", "cerrajero en Las Condes", etc.
    """
    priority = 0.9
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return (
            Provider.objects
            .filter(is_active=True)
            .values('category__slug', 'commune__slug')
            .annotate(n=Count('id'))
            .filter(n__gt=0)
            .order_by('commune__slug', 'category__slug')
        )

    def location(self, item):
        return f"/servicios/?categoria={item['category__slug']}&comuna={item['commune__slug']}"


class CommunitySitemap(Sitemap):
    """Una URL por cada comuna que tenga al menos 1 provider activo."""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return (
            Commune.objects
            .filter(is_active=True, providers__is_active=True)
            .distinct()
            .order_by('slug')
        )

    def location(self, obj):
        return f'/servicios/?comuna={obj.slug}'
