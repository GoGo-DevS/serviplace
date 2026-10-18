"""El catálogo de categorías agrupado, para la portada, el listado y la landing.

Una sola consulta con el conteo de perfiles activos anotado: la portada pinta
27 categorías y no puede hacer una consulta por cada una (G-04).
"""
from collections import Counter

from django.db.models import Count, F, Q

from .models import Category, Provider


def categorias_por_grupo(solo_grupos=None):
    """[{clave, nombre, descripcion, categorias:[Category con .n_activos]}], en el orden de GRUPOS."""
    categorias = list(
        Category.objects.filter(is_active=True)
        # Solo perfiles públicos (con dueño): los importados no cuentan. Suma
        # quien lo tiene de principal y quien lo tiene entre sus otros rubros.
        .annotate(n_activos=Count('providers', filter=Q(providers__is_active=True, providers__owner__isnull=False),
                                  distinct=True)
                  + Count('providers_secundarios',
                          filter=Q(providers_secundarios__is_active=True, providers_secundarios__owner__isnull=False)
                          & ~Q(providers_secundarios__category=F('pk')), distinct=True))
        .order_by('display_order', 'name')
    )
    grupos = []
    for clave, nombre, descripcion in Category.GRUPOS:
        if solo_grupos and clave not in solo_grupos:
            continue
        del_grupo = [c for c in categorias if c.group == clave]
        if del_grupo:
            grupos.append({
                'clave': clave,
                'slug': Category.GROUP_SLUGS[clave],
                'nombre': nombre,
                'descripcion': descripcion,
                'categorias': del_grupo,
                'total': sum(c.n_activos for c in del_grupo),
            })
    return grupos


def perfiles_por_rubro(publicos):
    """{slug: n} contando el rubro principal Y los otros rubros de cada perfil.

    Toda página que decide si enlazar un listado (vacío = 404) cuenta con esto:
    si contara solo el principal, un listado con perfiles quedaría sin enlace.
    """
    conteo = Counter(dict(publicos.order_by().values_list('category__slug').annotate(n=Count('id'))))
    otros = (Provider.otras_categorias.through.objects
             .filter(provider__in=publicos).exclude(category=F('provider__category'))
             .order_by().values_list('category__slug').annotate(n=Count('provider_id', distinct=True)))
    conteo.update(dict(otros))
    return conteo


def grupos_de(publicos):
    """Los grupos con al menos un perfil, por rubro principal o por otro rubro."""
    grupos = set(publicos.order_by().values_list('category__group', flat=True).distinct())
    grupos |= set(Provider.otras_categorias.through.objects.filter(provider__in=publicos)
                  .order_by().values_list('category__group', flat=True).distinct())
    return grupos
