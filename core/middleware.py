from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class DominioCanonicoMiddleware:
    """Un solo dominio para Google (18-10-2026).

    serviplace-60so.onrender.com respondía 200 con el sitio entero: una copia de
    cada página que Google podía indexar compitiendo con serviplace.cl. Todo
    GET/HEAD que llega por el hostname de Render se redirige (301) al mismo path
    en el dominio de SITE_URL. Sin RENDER_EXTERNAL_HOSTNAME (local, pruebas) no
    hace nada. www y http ya los redirige Cloudflare.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        canonico = urlsplit(settings.SITE_URL).hostname
        externo = settings.RENDER_EXTERNAL_HOSTNAME
        self.hosts_ajenos = {externo} if externo and canonico and externo != canonico else set()

    def __call__(self, request):
        if (self.hosts_ajenos and request.method in ('GET', 'HEAD')
                and request.get_host().split(':')[0] in self.hosts_ajenos):
            return HttpResponsePermanentRedirect(settings.SITE_URL + request.get_full_path())
        return self.get_response(request)
