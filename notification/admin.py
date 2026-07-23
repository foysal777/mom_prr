from django.contrib import admin
from .models import Device

# Register your models here.

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'user', 'platform', 'model', 'os_version', 'app_version', 'updated_at')
    list_filter = ('platform', 'created_at', 'updated_at')
    search_fields = ('device_id', 'push_token', 'user__email', 'user__username', 'model')
    readonly_fields = ('created_at', 'updated_at')
