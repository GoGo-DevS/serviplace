import unicodedata
from functools import lru_cache

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def otros_rubros(provider, mostrado):
    """Nombres de los rubros del perfil, menos el que ya muestra la tarjeta."""
    pk = getattr(mostrado, 'pk', None)
    return [c.name for c in provider.rubros if c.pk != pk]


# ── Íconos (20-11-2026, Diego: "la wea tiene que verse clean") ──────────────
# Trazos simples a 24x24, en el color del texto (currentColor). Son SVG en línea:
# no suman pedidos al servidor ni dependen de una librería de íconos.
_TRAZOS = {
    'gota': '<path d="M12 2.7s6 6.3 6 11a6 6 0 0 1-12 0c0-4.7 6-11 6-11z"/>',
    'rayo': '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    'llave': '<circle cx="7.5" cy="15.5" r="4.5"/><path d="m10.7 12.3 9.8-9.8M17 5l2.5 2.5M14.5 7.5 17 10"/>',
    'copo': '<path d="M12 2v20M4.9 4.9l14.2 14.2M2 12h20M4.9 19.1 19.1 4.9"/>',
    'martillo': '<path d="m14 10-9.3 9.3a1.8 1.8 0 0 1-2.6-2.6L11.4 7.4"/><path d="m12 6 3-3 6 6-3 3-2-1-3 3-2-2 3-3z"/>',
    'llama': '<path d="M12 22a7 7 0 0 0 7-7c0-4-3-6-4-9-1 3-3 4-3 4s-1-2-2-4c-2 3-5 5-5 9a7 7 0 0 0 7 7z"/>',
    'brillo': '<path d="M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2 2.2.8-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    'hoja': '<path d="M11 20A7 7 0 0 1 4 13c0-6 7-10 16-10 0 9-4 17-9 17z"/><path d="M4 21c4-6 8-9 12-11"/>',
    'brocha': '<path d="M18.4 2.6a2 2 0 0 1 3 3L11 16l-3-3z"/><path d="M8 13c-2 0-4 1.5-4 4 0 1.5-1 2.5-2 3 5 1 9-1 9-4"/>',
    'escudo': '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/>',
    'auto': '<path d="M5 17h14v-5l-2-5H7l-2 5z"/><path d="M5 12h14"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/>',
    'pulso': '<path d="M19.5 12.6 12 20l-7.5-7.4A5 5 0 0 1 12 6a5 5 0 0 1 7.5 6.6z"/><path d="M3.5 12h4l2-3 3 6 2-3h6"/>',
    'birrete': '<path d="M22 10 12 5 2 10l10 5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>',
    'tijera': '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12"/>',
    'maletin': '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>',
    'codigo': '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    'camara': '<path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="4"/>',
    'camion': '<path d="M3 6h11v10H3zM14 9h4l3 3v4h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    'tienda': '<path d="M3 9l1.5-5h15L21 9"/><path d="M4 9v11h16V9"/><path d="M3 9h18"/><path d="M9 20v-6h6v6"/>',
    'pesa': '<path d="M6 6v12M18 6v12M3 9v6M21 9v6M6 12h12"/>',
    'nota': '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    'globo': '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-6.4A8 8 0 1 1 21 12z"/>',
    'balanza': '<path d="M12 3v18M7 21h10M5 7h14M5 7l-3 7a3 3 0 0 0 6 0zM19 7l-3 7a3 3 0 0 0 6 0z"/>',
    'calculadora': '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h2M14 11h2M8 15h2M14 15h2M8 19h8"/>',
    'pluma': '<path d="M17 3l4 4L8 20H4v-4z"/>',
    'edificio': '<path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/>',
    'parlante': '<path d="M3 11v2a2 2 0 0 0 2 2h2l6 4V5L7 9H5a2 2 0 0 0-2 2zM17 8a5 5 0 0 1 0 8"/>',
    'calendario': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    'polera': '<path d="M20.4 6.6 16 3h-2a2 2 0 0 1-4 0H8L3.6 6.6 6 10l2-1v12h8V9l2 1z"/>',
    'torta': '<path d="M4 21h16v-8H4zM4 16c2 1 4 1 6 0s4-1 6 0 4 1 4 0M12 13V8"/><circle cx="12" cy="5" r="1.5"/>',
    'pieza': '<path d="M4 7h4a2 2 0 1 1 4 0h4v4a2 2 0 1 1 0 4v4H4v-4a2 2 0 1 0 0-4z"/>',
    'corazon': '<path d="M19.5 12.6 12 20l-7.5-7.4A5 5 0 0 1 12 6a5 5 0 0 1 7.5 6.6z"/>',
    # Modalidades
    'casa': '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
    'local': '<path d="M3 21h18M5 21V5h14v16"/><path d="M9 9h2M13 9h2M9 13h2M13 13h2M10 21v-4h4v4"/>',
    'pantalla': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
}

_ICONO_RUBRO = {
    'gasfiteria': 'gota', 'electricidad': 'rayo', 'cerrajeria': 'llave', 'climatizacion': 'copo',
    'construccion': 'martillo', 'carpinteria': 'martillo', 'soldadura': 'llama', 'limpieza': 'brillo',
    'jardineria': 'hoja', 'pintura': 'brocha', 'seguridad-hogar': 'escudo', 'mecanica-automotriz': 'auto',
    'repuestos-automotrices': 'auto', 'automotoras': 'auto', 'entrenamiento-personal': 'pesa',
    'cuidado-de-personas': 'corazon', 'clases-de-musica': 'nota', 'idiomas': 'globo', 'traduccion': 'globo',
    'peluqueria': 'tijera', 'tatuajes': 'pluma', 'contabilidad': 'calculadora', 'diseno-grafico': 'pluma',
    'estampado-y-ropa-personalizada': 'polera', 'uniformes-y-ropa-de-trabajo': 'polera',
    'fotografia-y-video': 'camara', 'edicion-de-video': 'camara', 'soporte-computacional': 'pantalla',
    'desarrollo-web': 'codigo', 'marketing-y-rrpp': 'parlante', 'produccion-de-eventos': 'calendario',
    'asesoria-legal': 'balanza', 'arquitectura': 'edificio', 'reposteria-y-dulces': 'torta', 'juguetes': 'pieza',
    'kinesiologia': 'pulso', 'psicologia': 'corazon', 'nutricion': 'pulso', 'fonoaudiologia': 'pulso',
    'terapia-ocupacional': 'pulso', 'enfermeria': 'pulso', 'podologia': 'pulso',
    'clases-particulares': 'birrete', 'psicopedagogia': 'birrete',
    'manicure-y-estetica': 'brillo', 'belleza-integral': 'brillo', 'maquillaje-profesional': 'brillo',
    'maquillaje-y-cosmetica': 'brillo', 'masajes-y-spa': 'corazon', 'fletes-y-logistica': 'camion',
    'traslados-y-turismo': 'camion',
}
_ICONO_GRUPO = {
    'hogar': 'martillo', 'salud': 'pulso', 'educacion': 'birrete', 'belleza': 'tijera',
    'profesional': 'maletin', 'transporte': 'camion', 'tiendas': 'tienda',
}


def svg(nombre, clase='ico'):
    return mark_safe(
        f'<svg class="{clase}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_TRAZOS[nombre]}</svg>')


def nombre_icono_rubro(rubro):
    """El nombre del ícono de un rubro: el suyo si lo tiene, si no el de su grupo.
    Lo usan la tarjeta del sitio y la historia de Instagram (directory/historia.py)."""
    return _ICONO_RUBRO.get(getattr(rubro, 'slug', ''), _ICONO_GRUPO.get(getattr(rubro, 'group', ''), 'maletin'))


@register.simple_tag
def icono_rubro(rubro):
    """El ícono de un rubro: el suyo si lo tiene, si no el de su grupo."""
    return svg(nombre_icono_rubro(rubro), 'ico ico-rubro')


@register.simple_tag
def icono(nombre, clase='ico'):
    return svg(nombre, clase)


# ── Logo de la institución donde estudió (20-11-2026) ──────────────────────
# El campo es texto libre ("INACAP sede Maipú", "Duoc UC"…): se reconoce por
# palabras clave, sin tildes ni mayúsculas. El logo se muestra solo si el archivo
# está en static/img/instituciones/; si no, queda el nombre, como siempre.
_INSTITUCIONES = [
    ('inacap', ('inacap',)),
    ('duoc', ('duoc',)),
    ('uchile', ('universidad de chile', 'u. de chile', 'uchile')),
    ('usach', ('usach', 'universidad de santiago')),
    ('uc', ('pontificia universidad catolica', 'universidad catolica de chile', 'puc ')),
    ('santo-tomas', ('santo tomas',)),
    ('aiep', ('aiep',)),
    ('ipchile', ('ipchile', 'ip chile', 'instituto profesional de chile')),
    ('unab', ('andres bello', 'unab')),
    ('udec', ('universidad de concepcion', 'udec')),
    ('utfsm', ('federico santa maria', 'utfsm', 'usm ')),
    ('uv', ('universidad de valparaiso',)),
    ('udla', ('universidad de las americas', 'udla')),
    ('umayor', ('universidad mayor',)),
    ('ucentral', ('universidad central',)),
]


def _normal(texto):
    texto = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode()
    return f' {texto.lower().strip()} '


def clave_institucion(nombre):
    """La clave del logo para un nombre de institución escrito a mano, o ''."""
    t = _normal(nombre)
    for clave, palabras in _INSTITUCIONES:
        if any(p in t for p in palabras):
            return clave
    return ''


@lru_cache(maxsize=64)
def _ruta_logo(clave):
    for ext in ('svg', 'webp', 'png'):
        ruta = f'img/instituciones/{clave}.{ext}'
        if finders.find(ruta):
            return ruta
    return ''


@register.simple_tag
def logo_institucion(nombre):
    """<img> con el logo de la institución si lo tenemos; vacío si no."""
    clave = clave_institucion(nombre)
    ruta = _ruta_logo(clave) if clave else ''
    if not ruta:
        return ''
    return format_html('<img class="logo-inst" src="{}" alt="" loading="lazy" height="18">', static(ruta))
