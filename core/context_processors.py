from django.conf import settings


def sitio(request):
    return {
        # Canonical por defecto: la URL sin parámetros. Una vista lo reemplaza
        # cuando corresponde (página 2 de un listado, búsqueda → /servicios/).
        'canonical_por_defecto': settings.SITE_URL + request.path,
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
        'DEFAULT_CONTACT_WHATSAPP': settings.DEFAULT_CONTACT_WHATSAPP,
    }
