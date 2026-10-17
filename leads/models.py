from django.db import models


class LeadEvent(models.Model):
    """Un paso del recorrido de quien busca o de quien publica.

    18-10-2026 — Pasa de registrar solo vistas de ficha y clics de WhatsApp a
    medir el embudo completo de los dos lados del directorio, para saber DÓNDE
    se pierde la oportunidad: si faltan perfiles (búsquedas sin resultados),
    si las fichas no convencen (vistas sin clic) o si el profesional se cae
    antes de publicar. Sin datos personales: ni IP ni nombre, solo un
    identificador anónimo que cambia cada día (ver leads/registro.py).

    Un clic en WhatsApp es intención de contacto, no una conversación ni un
    trabajo hecho: el panel lo dice así.
    """
    WHATSAPP_CLICK = 'whatsapp_click'
    DETAIL_VIEW = 'detail_view'
    SEARCH = 'search'
    PAGE_VIEW = 'page_view'
    SIGNUP_STARTED = 'signup_started'
    SIGNUP_DONE = 'signup_done'
    PROFILE_PUBLISHED = 'profile_published'

    EVENT_TYPES = [
        (WHATSAPP_CLICK, 'Click en WhatsApp'),
        (DETAIL_VIEW, 'Vista de detalle'),
        (SEARCH, 'Búsqueda'),
        (PAGE_VIEW, 'Visita a página clave'),
        (SIGNUP_STARTED, 'Registro iniciado'),
        (SIGNUP_DONE, 'Cuenta creada'),
        (PROFILE_PUBLISHED, 'Perfil publicado'),
    ]

    provider = models.ForeignKey(
        'directory.Provider', on_delete=models.CASCADE, related_name='lead_events', null=True, blank=True,
    )
    source_page = models.CharField(max_length=120)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    # Contexto de la búsqueda: slugs y una versión saneada del texto escrito
    # (sin números largos: un teléfono o un RUT no se guardan).
    category_slug = models.CharField(max_length=90, blank=True)
    commune_slug = models.CharField(max_length=90, blank=True)
    group = models.CharField(max_length=20, blank=True)
    query = models.CharField(max_length=80, blank=True)
    results_count = models.PositiveIntegerField(null=True, blank=True)
    visitor = models.CharField(
        max_length=16, blank=True,
        help_text='Hash anónimo que cambia cada día: cuenta visitantes sin poder seguir a nadie.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['event_type', 'created_at'])]
        verbose_name = 'evento de lead'
        verbose_name_plural = 'eventos de leads'

    def __str__(self):
        return f'{self.get_event_type_display()} - {self.provider or self.source_page}'
