"""El catálogo de categorías agrupado, para la portada, el listado y la landing.

Una sola consulta con el conteo de perfiles activos anotado: la portada pinta
27 categorías y no puede hacer una consulta por cada una (G-04).
"""
from django.db.models import Count, Q

from .models import Category


def categorias_por_grupo(solo_grupos=None):
    """[{clave, nombre, descripcion, categorias:[Category con .n_activos]}], en el orden de GRUPOS."""
    categorias = list(
        Category.objects.filter(is_active=True)
        # Solo perfiles públicos (con dueño): los importados no cuentan.
        .annotate(n_activos=Count('providers', filter=Q(providers__is_active=True, providers__owner__isnull=False)))
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
