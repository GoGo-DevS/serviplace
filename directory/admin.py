from django.contrib import admin, messages
from django.utils import timezone

from .models import Category, Commune, Provider, ProviderApplication, ProviderImage, ProviderReport, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'slug', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'slug', 'region__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'pide_registro_salud', 'slug', 'display_order', 'is_active')
    list_filter = ('group', 'pide_registro_salud', 'is_active')
    list_editable = ('display_order',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class ProviderImageInline(admin.TabularInline):
    model = ProviderImage
    extra = 0
    fields = ('image', 'alt_text', 'is_cover', 'display_order')


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        'business_name',
        'category',
        'commune',
        'sector',
        'is_verified',
        'is_featured',
        'is_active',
        'data_status',
        'whatsapp_clicks_count',
        'views_count',
        'updated_at',
    )
    list_editable = ('is_verified', 'is_featured', 'is_active')
    list_filter = ('category__group', 'category', 'commune', 'data_status', 'is_verified', 'is_featured', 'is_active')
    search_fields = (
        'business_name',
        'contact_name',
        'sector',
        'description',
        'short_description',
        'phone',
        'whatsapp_number',
        'source_name',
        'source_url',
        'source_notes',
    )
    prepopulated_fields = {'slug': ('business_name',)}
    readonly_fields = ('views_count', 'whatsapp_clicks_count', 'claimed_at', 'created_at', 'updated_at')
    inlines = [ProviderImageInline]
    fieldsets = (
        ('Información principal', {'fields': ('business_name', 'slug', 'contact_name', 'category', 'short_description', 'description')}),
        ('Contacto', {'fields': ('phone', 'whatsapp_number', 'email')}),
        ('Ubicación y zona de atención', {'fields': ('commune', 'sector', 'address', 'service_area')}),
        ('Perfil profesional', {'fields': (
            'profession_title', 'institution', 'graduation_year', 'health_registry',
            'attends_home', 'attends_office', 'attends_online',
        )}),
        ('Estado del perfil', {'fields': ('is_verified', 'is_featured', 'is_active', 'data_status', 'owner', 'claimed_at')}),
        ('Suscripción', {'fields': ('subscription_status', 'subscription_expires_at')}),
        ('Trazabilidad de fuente', {'fields': ('source_name', 'source_url', 'source_notes')}),
        ('Métricas', {'fields': ('views_count', 'whatsapp_clicks_count', 'created_at', 'updated_at')}),
    )


@admin.register(ProviderImage)
class ProviderImageAdmin(admin.ModelAdmin):
    list_display = ('provider', 'alt_text', 'is_cover', 'display_order')
    list_filter = ('is_cover', 'provider__category', 'provider__commune')
    search_fields = ('provider__business_name', 'alt_text')


@admin.register(ProviderApplication)
class ProviderApplicationAdmin(admin.ModelAdmin):
    list_display = ('nombre_negocio', 'nombre_contacto', 'categoria', 'sector', 'whatsapp', 'status', 'created_at')
    list_filter = ('status', 'categoria', 'created_at')
    search_fields = ('nombre_negocio', 'nombre_contacto', 'telefono', 'whatsapp', 'sector', 'descripcion_servicio')
    readonly_fields = ('created_at',)
    list_editable = ('status',)
    fieldsets = (
        ('Datos del servicio', {'fields': ('nombre_negocio', 'nombre_contacto', 'categoria', 'sector', 'descripcion_servicio')}),
        ('Experiencia y presencia digital', {'fields': ('anos_experiencia', 'horario_atencion', 'instagram', 'website')}),
        ('Contacto', {'fields': ('telefono', 'whatsapp', 'acepta_contacto')}),
        ('Gestión', {'fields': ('status', 'created_at')}),
    )


@admin.register(ProviderReport)
class ProviderReportAdmin(admin.ModelAdmin):
    """Reportes, bajas, correcciones y reclamos que llegan del público.

    Hasta el 17-10-2026 no estaba registrado: lo que llegara era invisible.
    Reclamar NO asigna el perfil solo (cualquiera con cuenta podría quedarse
    con el teléfono de un negocio real): se aprueba acá, después de
    confirmar por el WhatsApp del perfil que quien reclama es el dueño.
    """
    list_display = ('provider', 'kind', 'claimant', 'reporter_name', 'reporter_contact',
                    'spam_flag', 'created_at', 'resolved_at')
    list_filter = ('kind', 'spam_flag', ('resolved_at', admin.EmptyFieldListFilter))
    search_fields = ('provider__business_name', 'reporter_name', 'reporter_contact', 'message')
    raw_id_fields = ('provider', 'claimant')
    readonly_fields = ('created_at', 'created_ip', 'spam_reasons')
    actions = ['aprobar_reclamo', 'marcar_resuelto']

    @admin.action(description='Aprobar reclamo: el perfil pasa a ser de quien lo reclamó')
    def aprobar_reclamo(self, request, queryset):
        aprobados, saltados = 0, 0
        for reporte in queryset.select_related('provider', 'claimant'):
            perfil = reporte.provider
            if (reporte.kind != ProviderReport.CLAIM or reporte.claimant is None
                    or reporte.resolved_at or perfil.owner_id):
                saltados += 1
                continue
            perfil.owner = reporte.claimant
            perfil.claimed_at = timezone.now()
            perfil.data_status = Provider.AUTHORIZED
            perfil.save(update_fields=['owner', 'claimed_at', 'data_status', 'updated_at'])
            reporte.resolved_at = timezone.now()
            reporte.resolution_note = f'Reclamo aprobado por {request.user.username}.'
            reporte.save(update_fields=['resolved_at', 'resolution_note'])
            aprobados += 1
        self.message_user(request, f'{aprobados} reclamo(s) aprobado(s).', messages.SUCCESS)
        if saltados:
            self.message_user(
                request,
                f'{saltados} omitido(s): no eran reclamos, ya estaban resueltos o el perfil ya tenía dueño.',
                messages.WARNING,
            )

    @admin.action(description='Marcar como resuelto')
    def marcar_resuelto(self, request, queryset):
        n = queryset.filter(resolved_at__isnull=True).update(
            resolved_at=timezone.now(), resolution_note=f'Resuelto por {request.user.username}.')
        self.message_user(request, f'{n} marcado(s) como resuelto(s).', messages.SUCCESS)
