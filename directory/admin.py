from django.contrib import admin

from .models import Category, Commune, Provider, ProviderApplication, ProviderImage, Region


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
    list_display = ('name', 'slug', 'display_order', 'is_active')
    list_filter = ('is_active',)
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
    list_filter = ('commune', 'category', 'data_status', 'is_verified', 'is_featured', 'is_active')
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
    readonly_fields = ('views_count', 'whatsapp_clicks_count', 'created_at', 'updated_at')
    inlines = [ProviderImageInline]
    fieldsets = (
        ('Información principal', {'fields': ('business_name', 'slug', 'contact_name', 'category', 'short_description', 'description')}),
        ('Contacto', {'fields': ('phone', 'whatsapp_number', 'email')}),
        ('Ubicación y zona de atención', {'fields': ('commune', 'sector', 'address', 'service_area')}),
        ('Estado del perfil', {'fields': ('is_verified', 'is_featured', 'is_active', 'data_status')}),
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
