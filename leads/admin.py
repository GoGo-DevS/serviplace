from django.contrib import admin

from .models import LeadEvent


@admin.register(LeadEvent)
class LeadEventAdmin(admin.ModelAdmin):
    list_display = ('provider', 'event_type', 'source_page', 'created_at')
    list_filter = ('event_type', 'provider__commune', 'provider__category', 'created_at')
    search_fields = ('provider__business_name', 'source_page')
    readonly_fields = ('provider', 'event_type', 'source_page', 'created_at')

# Register your models here.
