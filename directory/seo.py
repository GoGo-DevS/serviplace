"""SEO técnico de ServiPlace: JSON-LD y migas de pan (18-10-2026).

Sigue el checklist de la auditoría de Jorge Urzúa (memoria checklist-seo-tecnico):
  - el schema de la ORGANIZACIÓN va solo en la portada; el resto la referencia
    por @id, para que Google lea una sola entidad y no una por página;
  - la miga recorre la jerarquía completa (Inicio > Servicios > Gásfiter >
    Maipú > perfil): una miga que se salta niveles no los enlaza;
  - cada listado es CollectionPage + ItemList;
  - cada ficha declara el tipo de negocio que es (Plumber, Electrician…).
"""
import json

from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

# Tipo de schema.org por especialidad. Lo que no está acá es ProfessionalService.
TIPO_SCHEMA = {
    'gasfiteria': 'Plumber',
    'electricidad': 'Electrician',
    'cerrajeria': 'Locksmith',
    'climatizacion': 'HVACBusiness',
    'construccion': 'GeneralContractor',
    'pintura': 'HousePainter',
    'carpinteria': 'HomeAndConstructionBusiness',
    'jardineria': 'HomeAndConstructionBusiness',
    'limpieza': 'HomeAndConstructionBusiness',
    'kinesiologia': 'Physiotherapy',
    'peluqueria': 'HairSalon',
    'manicure-y-estetica': 'NailSalon',
    'contabilidad': 'AccountingService',
}


def _url(path):
    return f'{settings.SITE_URL}{path}'


def id_organizacion():
    return _url('/#organizacion')


def id_sitio():
    return _url('/#sitio')


def como_script(*bloques):
    """<script type="application/ld+json"> por bloque. `</` escapado: un texto
    con "</script>" escrito por un usuario no puede cerrar el bloque."""
    salida = []
    for bloque in bloques:
        if not bloque:
            continue
        texto = json.dumps(bloque, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
        salida.append(f'<script type="application/ld+json">{texto}</script>')
    return mark_safe('\n'.join(salida))


def organizacion_y_sitio():
    """Solo para la portada."""
    return {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'Organization',
                '@id': id_organizacion(),
                'name': 'ServiPlace',
                'url': _url('/'),
                'logo': _url(static('img/marca/serviplace-app-512.png')),
                'description': settings.SITE_DESCRIPTION,
                'areaServed': {'@type': 'Country', 'name': 'Chile'},
                'parentOrganization': {
                    '@type': 'Organization',
                    'name': 'GoGoDevS',
                    'url': 'https://gogodevs.cl/',
                },
            },
            {
                '@type': 'WebSite',
                '@id': id_sitio(),
                'name': 'ServiPlace',
                'url': _url('/'),
                'inLanguage': 'es-CL',
                'publisher': {'@id': id_organizacion()},
                'potentialAction': {
                    '@type': 'SearchAction',
                    'target': {'@type': 'EntryPoint', 'urlTemplate': _url('/servicios/?q={consulta}')},
                    'query-input': 'required name=consulta',
                },
            },
        ],
    }


def miga(pasos):
    """pasos = [(nombre, path)]; el último es la página actual."""
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': nombre, 'item': _url(path)}
            for i, (nombre, path) in enumerate(pasos, start=1)
        ],
    }


def listado(nombre, path, perfiles, total):
    return {
        '@context': 'https://schema.org',
        '@type': 'CollectionPage',
        'name': nombre,
        'url': _url(path),
        'isPartOf': {'@id': id_sitio()},
        'mainEntity': {
            '@type': 'ItemList',
            'numberOfItems': total,
            'itemListElement': [
                {'@type': 'ListItem', 'position': i, 'url': _url(p.get_absolute_url()), 'name': p.business_name}
                for i, p in enumerate(perfiles, start=1)
            ],
        },
    }


def perfil(provider, request):
    datos = {
        '@context': 'https://schema.org',
        '@type': TIPO_SCHEMA.get(provider.category.slug, 'ProfessionalService'),
        '@id': _url(provider.get_absolute_url()) + '#perfil',
        'name': provider.business_name,
        'url': _url(provider.get_absolute_url()),
        'description': provider.short_description,
        'telephone': provider.phone,
        'address': {
            '@type': 'PostalAddress',
            'addressLocality': provider.commune.name,
            'addressRegion': provider.commune.region.name if provider.commune.region_id else '',
            'addressCountry': 'CL',
        },
        'areaServed': provider.service_area or provider.commune.name,
        'isPartOf': {'@id': id_sitio()},
    }
    if provider.foto:
        url = provider.foto.url
        datos['image'] = request.build_absolute_uri(url) if url.startswith('/') else url
    if provider.profession_title:
        datos['knowsAbout'] = provider.profession_title
    return datos
