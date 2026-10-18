from django.conf import settings

# Pantallas que NO se mandan a Google: el panel del profesional, sus métricas,
# la edición de su perfil y el admin. Registro y publicar SÍ se miden: son los
# pasos del embudo de quien ofrece y no muestran datos de nadie más.
RUTAS_SIN_ANALITICA = ('/cuenta/dashboard/', '/cuenta/metricas/', '/cuenta/mi-perfil/', '/cuenta/login/')


def _ga4_id(request):
    ga4 = settings.GA4_MEASUREMENT_ID
    if not ga4 or request.path.startswith(RUTAS_SIN_ANALITICA):
        return ''
    if settings.ADMIN_URL and request.path.startswith('/' + settings.ADMIN_URL):
        return ''
    usuario = getattr(request, 'user', None)
    if usuario is not None and usuario.is_authenticated and usuario.is_staff:
        return ''  # las visitas de Diego no son tráfico
    return ga4


def sitio(request):
    return {
        # Canonical por defecto: la URL sin parámetros. Una vista lo reemplaza
        # cuando corresponde (página 2 de un listado, búsqueda → /servicios/).
        'canonical_por_defecto': settings.SITE_URL + request.path,
        'ga4_id': _ga4_id(request),
        # Eventos que se dispararon en el paso anterior (registro, publicar) y
        # se informan UNA vez en la página siguiente.
        'ga4_eventos': request.session.pop('ga4_eventos', []) if hasattr(request, 'session') else [],
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
        'DEFAULT_CONTACT_WHATSAPP': settings.DEFAULT_CONTACT_WHATSAPP,
    }
