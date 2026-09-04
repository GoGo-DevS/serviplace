"""
Filtro antispam para formularios públicos (registro, publicar, reportar).

Tres señales; hace falta más de una para marcar (un solo enlace pegado NO marca):
  - honeypot: campo de texto fuera de pantalla que un humano no ve ni llena
  - sello de tiempo firmado: el formulario se envió antes de N segundos de haberse dibujado
  - vocabulario: enlaces en cantidad o palabras típicas de spam de backlinks

Lo marcado como spam SE GUARDA con la marca — nunca se rechaza. Un falso positivo
rechazado es un prestador real perdido sin que nadie se entere.
"""
import re
import time

from django import forms
from django.core import signing
from django.utils import timezone

HONEYPOT_FIELD = 'sitio_web_confirmacion'
TIMESTAMP_FIELD = 'sello_formulario'
MIN_SECONDS = 3
SPAM_THRESHOLD = 40

_URL_RE = re.compile(r'https?://|www\.', re.IGNORECASE)
_SPAM_WORDS = re.compile(
    r'\b(backlinks?|seo\s+(services?|agency|company)|guest\s*post|link\s*building|'
    r'casino|crypto|bitcoin|forex|viagra|cialis|escorts?|porn|xxx|'
    r'domain\s+authority|dofollow|buy\s+followers|telegram\s*@)\b',
    re.IGNORECASE,
)


def sello_nuevo():
    return signing.dumps(int(time.time()), salt='antispam')


def _edad_sello(valor):
    try:
        emitido = signing.loads(valor, salt='antispam', max_age=60 * 60 * 6)
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return None
    return time.time() - int(emitido)


def evaluar(post_data, textos):
    """
    Devuelve (score, motivos). `textos` = campos de texto libre a inspeccionar.
    score >= SPAM_THRESHOLD => spam.
    """
    score = 0
    motivos = []

    if (post_data.get(HONEYPOT_FIELD) or '').strip():
        score += 40
        motivos.append('honeypot')

    edad = _edad_sello(post_data.get(TIMESTAMP_FIELD, ''))
    if edad is None:
        score += 20
        motivos.append('sin_sello')
    elif edad < MIN_SECONDS:
        score += 30
        motivos.append(f'rapido_{edad:.1f}s')

    texto = ' '.join(t or '' for t in textos)
    urls = len(_URL_RE.findall(texto))
    if urls >= 3:
        score += 30
        motivos.append(f'urls_{urls}')
    elif urls == 2:
        score += 20
        motivos.append('urls_2')
    if _SPAM_WORDS.search(texto):
        score += 20
        motivos.append('vocabulario')

    return score, ','.join(motivos)


def es_spam(post_data, textos):
    score, motivos = evaluar(post_data, textos)
    return score >= SPAM_THRESHOLD, motivos


class AntispamFormMixin(forms.Form):
    """Agrega honeypot + sello firmado. El template debe dibujar el honeypot fuera de pantalla."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[HONEYPOT_FIELD] = forms.CharField(
            required=False,
            label='Deja este campo vacío',
            widget=forms.TextInput(attrs={
                'autocomplete': 'off',
                'tabindex': '-1',
                'aria-hidden': 'true',
                'class': 'hp-field',
            }),
        )
        self.fields[TIMESTAMP_FIELD] = forms.CharField(
            required=False,
            initial=sello_nuevo,
            widget=forms.HiddenInput(),
        )

    def antispam_textos(self):
        """Sobrescribir: lista de textos libres a inspeccionar."""
        return []

    def evaluar_spam(self):
        return es_spam(self.data, self.antispam_textos())


def ip_cliente(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()[:45]
    return (request.META.get('REMOTE_ADDR') or '')[:45] or None


def excede_limite_ip(model, ip, limite, minutos, campo='created_ip'):
    """Cuenta filas creadas desde la misma IP en la ventana. Persistente (DB), sirve con varios workers."""
    if not ip:
        return False
    desde = timezone.now() - timezone.timedelta(minutes=minutos)
    return model.objects.filter(**{campo: ip, 'created_at__gte': desde}).count() >= limite
