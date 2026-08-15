from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = [
        'device_id',
        'user',
        'platform',
        'model',
        'os_version',
        'app_version',
        'created_at',
        'updated_at'
    ]
    list_filter = ['platform', 'created_at', 'updated_at']
    search_fields = [
        'device_id',
        'push_token',
        'user__email',
        'user__username',
        'user__full_name',
        'model'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
