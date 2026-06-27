from django.db import models


class LeadEvent(models.Model):
    WHATSAPP_CLICK = 'whatsapp_click'
    DETAIL_VIEW = 'detail_view'

    EVENT_TYPES = [
        (WHATSAPP_CLICK, 'Click en WhatsApp'),
        (DETAIL_VIEW, 'Vista de detalle'),
    ]

    provider = models.ForeignKey('directory.Provider', on_delete=models.CASCADE, related_name='lead_events')
    source_page = models.CharField(max_length=120)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'evento de lead'
        verbose_name_plural = 'eventos de leads'

    def __str__(self):
        return f'{self.get_event_type_display()} - {self.provider}'

# Create your models here.
