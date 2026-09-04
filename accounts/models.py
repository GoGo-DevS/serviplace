import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    whatsapp = models.CharField(max_length=30, blank=True)
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals'
    )
    spam_flag = models.BooleanField(default=False, help_text='El registro disparó el filtro antispam.')
    spam_reasons = models.CharField(max_length=200, blank=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuarios'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    @property
    def referral_url(self):
        from django.urls import reverse
        return f"{reverse('core:home')}?ref={self.referral_code}"
