from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'region'
        verbose_name_plural = 'regiones'

    def __str__(self):
        return self.name


class Commune(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='communes', null=True, blank=True)
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'comuna'
        verbose_name_plural = 'comunas'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, blank=True, help_text='Nombre corto o emoji visible.')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.name


class Provider(models.Model):
    PUBLIC_PROSPECT = 'prospecto_publico'
    CONTACTED = 'contactado'
    AUTHORIZED = 'autorizado'
    REJECTED = 'rechazado'

    DATA_STATUS_CHOICES = [
        (PUBLIC_PROSPECT, 'Prospecto publico'),
        (CONTACTED, 'Contactado'),
        (AUTHORIZED, 'Autorizado'),
        (REJECTED, 'Rechazado'),
    ]

    FREE = 'free'
    VERIFIED_PAID = 'verified_paid'
    FEATURED_PAID = 'featured_paid'

    SUBSCRIPTION_CHOICES = [
        (FREE, 'Gratuito'),
        (VERIFIED_PAID, 'Verificado (pagado)'),
        (FEATURED_PAID, 'Destacado (pagado)'),
    ]

    business_name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    contact_name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='providers',
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='providers')
    commune = models.ForeignKey(Commune, on_delete=models.PROTECT, related_name='providers')
    sector = models.CharField(max_length=120)
    description = models.TextField()
    short_description = models.CharField(max_length=220)
    phone = models.CharField(max_length=30)
    whatsapp_number = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=180, blank=True)
    service_area = models.CharField(max_length=180, blank=True)
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    whatsapp_clicks_count = models.PositiveIntegerField(default=0)
    source_name = models.CharField(max_length=140, blank=True)
    source_url = models.URLField(blank=True)
    source_notes = models.TextField(blank=True)
    data_status = models.CharField(max_length=30, choices=DATA_STATUS_CHOICES, default=PUBLIC_PROSPECT)
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default=FREE)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    # Moderación (modelo Yapo con freno de emergencia)
    spam_flag = models.BooleanField(
        default=False,
        help_text='Marcado por el filtro antispam al publicar. Se guarda igual; un moderador decide.',
    )
    spam_reasons = models.CharField(max_length=200, blank=True)
    moderation_note = models.TextField(blank=True)
    hidden_at = models.DateTimeField(null=True, blank=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-is_verified', 'business_name']
        indexes = [
            models.Index(fields=['is_active', 'is_featured', 'is_verified']),
            models.Index(fields=['is_active', 'commune', 'category']),
            models.Index(fields=['is_active', 'data_status']),
            models.Index(fields=['business_name']),
            models.Index(fields=['slug']),
        ]
        verbose_name = 'prestador'
        verbose_name_plural = 'prestadores'

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f'{self.business_name}-{self.commune.name}')
            slug = base_slug
            counter = 2
            while Provider.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('directory:provider_detail', kwargs={'slug': self.slug})

    @property
    def clean_whatsapp_number(self):
        return ''.join(character for character in self.whatsapp_number if character.isdigit())

    @property
    def has_whatsapp(self):
        """Solo un móvil chileno (569 + 8 dígitos) recibe WhatsApp. Un fijo no."""
        digits = self.clean_whatsapp_number
        return len(digits) == 11 and digits.startswith('569')

    @property
    def is_claimed(self):
        return self.owner_id is not None

    @property
    def is_synthetic(self):
        return self.source_name == 'seed_offline'


class ProviderImage(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='providers/')
    alt_text = models.CharField(max_length=160, blank=True)
    is_cover = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', '-is_cover', 'id']
        verbose_name = 'imagen de prestador'
        verbose_name_plural = 'imagenes de prestadores'

    def __str__(self):
        return self.alt_text or f'Imagen de {self.provider}'


class ProviderApplication(models.Model):
    PENDING = 'pendiente'
    CONTACTED = 'contactado'
    APPROVED = 'aprobado'
    REJECTED = 'rechazado'

    STATUS_CHOICES = [
        (PENDING, 'Pendiente'),
        (CONTACTED, 'Contactado'),
        (APPROVED, 'Aprobado'),
        (REJECTED, 'Rechazado'),
    ]

    nombre_negocio = models.CharField(max_length=140)
    nombre_contacto = models.CharField(max_length=120)
    categoria = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='applications')
    telefono = models.CharField(max_length=30)
    whatsapp = models.CharField(max_length=30)
    instagram = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    anos_experiencia = models.PositiveSmallIntegerField(null=True, blank=True)
    horario_atencion = models.CharField(max_length=160, blank=True)
    sector = models.CharField(max_length=120)
    descripcion_servicio = models.TextField()
    acepta_contacto = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'postulacion de prestador'
        verbose_name_plural = 'postulaciones de prestadores'

    def __str__(self):
        return f'{self.nombre_negocio} - {self.get_status_display()}'


class ProviderReport(models.Model):
    """Reporte, solicitud de baja o corrección sobre un perfil. Lo llena el público."""
    REPORT = 'reporte'
    REMOVAL = 'baja'
    CORRECTION = 'correccion'
    KIND_CHOICES = [
        (REPORT, 'Reportar perfil'),
        (REMOVAL, 'Solicitar baja (soy el titular)'),
        (CORRECTION, 'Corregir datos'),
    ]

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='reports')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=REPORT)
    reporter_name = models.CharField(max_length=120, blank=True)
    reporter_contact = models.CharField(max_length=160, blank=True)
    message = models.TextField()
    created_ip = models.GenericIPAddressField(null=True, blank=True)
    spam_flag = models.BooleanField(default=False)
    spam_reasons = models.CharField(max_length=200, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'reporte de perfil'
        verbose_name_plural = 'reportes de perfiles'

    def __str__(self):
        return f'{self.get_kind_display()} · {self.provider}'

    @property
    def is_resolved(self):
        return self.resolved_at is not None
