from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect, reverse
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, SiteConfig, HelpSupport


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'email',
        'full_name',
        'username',
        'phone',
        'country',
        'email_verified',
        'is_staff',
        'is_active',
        'date_joined'
    ]
    list_filter = [
        'email_verified',
        'is_staff',
        'is_superuser',
        'is_active',
        'gender',
        'language',
        'date_joined'
    ]
    search_fields = [
        'email',
        'full_name',
        'username',
        'phone',
        'country',
        'device_token'
    ]
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'full_name',
                'username',
                'profile_image',
                'gender',
                'date_of_birth',
                'phone',
                'country',
                'language'
            )
        }),
        (_('Verification & Status'), {
            'fields': ('email_verified', 'otp', 'is_active', 'is_staff', 'is_superuser')
        }),
        (_('Device info'), {
            'classes': ('collapse',),
            'fields': (
                'device_token',
                'platform',
                'device_model',
                'os_version',
                'app_version',
                'device_id'
            )
        }),
        (_('Permissions'), {
            'classes': ('collapse',),
            'fields': ('groups', 'user_permissions')
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password', 'is_staff', 'is_active'),
        }),
    )


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'subscription_price_id',
        'moncash_subscription_price',
        'yearly_subscription_price_id',
        'yearly_moncash_subscription_price'
    ]

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def changelist_view(self, request, extra_context=None):
        obj = SiteConfig.objects.first()
        if obj:
            url = reverse(
                'admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name),
                args=[obj.pk]
            )
            return redirect(url)
        app_label = SiteConfig._meta.app_label
        model_name = SiteConfig._meta.model_name
        return redirect(reverse(f'admin:{app_label}_{model_name}_add'))


@admin.register(HelpSupport)
class HelpSupportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'email',
        'short_description',
        'is_solved'
    ]
    list_filter = [
        'is_solved'
    ]
    search_fields = [
        'email',
        'description',
        'answer'
    ]
    list_editable = [
        'is_solved'
    ]

    @admin.display(description='Description')
    def short_description(self, obj):
        return obj.description[:60] + ('...' if len(obj.description) > 60 else '')