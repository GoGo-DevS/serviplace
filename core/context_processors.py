from django.conf import settings


def sitio(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
        'DEFAULT_CONTACT_WHATSAPP': settings.DEFAULT_CONTACT_WHATSAPP,
    }
