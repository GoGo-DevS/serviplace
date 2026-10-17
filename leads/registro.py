"""Registro de eventos del embudo, sin datos personales y sin romper nada.

Tres reglas:
  1. Los bots no cuentan. Google, la previsualización de enlaces de WhatsApp y
     un `curl` de prueba inflaban las vistas y los clics de las fichas.
  2. Nada personal sale de acá: ni IP ni agente de usuario se guardan, solo un
     hash diario que permite contar visitantes y no permite seguir a nadie.
  3. Si registrar falla, la página igual responde: medir no puede tumbar la
     búsqueda ni el contacto.
"""
import hashlib
import logging
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.antispam import ip_cliente

from .models import LeadEvent

log = logging.getLogger(__name__)

_BOT_RE = re.compile(
    r'bot|crawl|spider|slurp|facebookexternalhit|whatsapp|telegram|preview|headless|'
    r'python-requests|python-urllib|curl|wget|httpx|go-http|monitor|uptime|lighthouse|render',
    re.IGNORECASE,
)
_NUMEROS_LARGOS = re.compile(r'\d[\d\s.\-]{5,}\d')


def es_bot(request):
    agente = request.META.get('HTTP_USER_AGENT', '')
    return not agente or bool(_BOT_RE.search(agente))


def visitante(request):
    """Hash de (día, secreto, IP, agente). Cambia a medianoche: no hay historial por persona."""
    base = f"{timezone.localdate().isoformat()}|{settings.SECRET_KEY}|{ip_cliente(request) or ''}|{request.META.get('HTTP_USER_AGENT', '')}"
    return hashlib.sha256(base.encode()).hexdigest()[:16]


def sanear_busqueda(texto):
    """Minúsculas, espacios simples, sin números largos (teléfonos, RUT), máx. 80."""
    texto = ' '.join((texto or '').lower().split())
    texto = _NUMEROS_LARGOS.sub('#', texto)
    return texto[:80]


def registrar(request, tipo, *, origen, provider=None, **campos):
    """Guarda un evento. Devuelve el evento, o None si era un bot o falló."""
    if es_bot(request):
        return None
    try:
        with transaction.atomic():
            return LeadEvent.objects.create(
                event_type=tipo, source_page=origen, provider=provider, visitor=visitante(request), **campos,
            )
    except Exception:  # noqa: BLE001 — medir nunca debe romper la página
        log.warning('No se pudo registrar el evento %s', tipo, exc_info=True)
        return None
