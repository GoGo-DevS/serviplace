from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'whatsapp', 'referral_code', 'referred_by', 'created_at']
    search_fields = ['user__username', 'user__email', 'referral_code']
    raw_id_fields = ['user', 'referred_by']
