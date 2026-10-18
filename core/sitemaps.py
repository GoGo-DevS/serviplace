"""Sitemap de ServiPlace (18-10-2026).

Reglas de la auditoría de Jorge (memoria checklist-seo-tecnico):
  - solo URLs limpias: nada de ?categoria=&comuna= (eso eran URLs paramétricas
    que dispersaban la autoridad);
  - solo URLs que responden 200: ni redirecciones (/sumate/ era una) ni
    listados vacíos (responden 404 a propósito);
  - las pruebas piden cada <loc>; no basta con leer el generador.
"""
from django.contrib.sitemaps import Sitemap
from django.db.models import Count, Max
from django.urls import reverse

from directory.models import Category, Provider


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['core:home', 'directory:provider_list', 'core:para_profesionales', 'core:about',
                'core:trust_and_safety', 'core:contact', 'core:terms', 'core:privacy']

    def location(self, item):
        return reverse(item)


class ListadosSitemap(Sitemap):
    """Especialidad, grupo, comuna y especialidad×comuna con al menos un perfil
    público. "Gásfiter en Maipú" es la página de más valor del sitio."""
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        publicos = Provider.objects.publicos()
        filas = []
        for fila in publicos.values('category__slug').annotate(n=Count('id'), mod=Max('updated_at')):
            filas.append((reverse('directory:listado_rubro', kwargs={'rubro': fila['category__slug']}), fila['mod'], 0.7))
        for fila in publicos.values('category__group').annotate(n=Count('id'), mod=Max('updated_at')):
            slug = Category.GROUP_SLUGS.get(fila['category__group'])
            if slug:
                filas.append((reverse('directory:listado_rubro', kwargs={'rubro': slug}), fila['mod'], 0.6))
        for fila in publicos.values('commune__slug').annotate(n=Count('id'), mod=Max('updated_at')):
            filas.append((reverse('directory:listado_comuna', kwargs={'comuna': fila['commune__slug']}), fila['mod'], 0.7))
        for fila in (publicos.values('category__slug', 'commune__slug')
                     .annotate(n=Count('id'), mod=Max('updated_at'))):
            filas.append((reverse('directory:listado_rubro_comuna',
                                  kwargs={'rubro': fila['category__slug'], 'comuna': fila['commune__slug']}),
                          fila['mod'], 0.9))
        return sorted(filas)

    def location(self, item):
        return item[0]

    def lastmod(self, item):
        return item[1]

    def priority(self, item):
        return item[2]


class ProviderSitemap(Sitemap):
    priority = 0.6
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return Provider.objects.publicos().only('slug', 'updated_at').order_by('slug')

    def lastmod(self, obj):
        return obj.updated_at
