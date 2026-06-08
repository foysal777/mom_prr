from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect, reverse

from .models import CustomUser, SiteConfig, HelpSupport
# If using default User model, this is already enabled
# Just make sure you're using UserAdmin
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'device_token']
    pass


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
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
        print(app_label, model_name)
        return redirect(reverse(f'admin:{app_label}_{model_name}_add'))
        return super().changelist_view(request, extra_context)


@admin.register(HelpSupport)
class HelpSupportAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'is_solved'
    ]
    list_filter = [
        'is_solved'
    ]


# @admin.register()