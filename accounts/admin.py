from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
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
        'watched_movies_count',
        'watched_series_count',
        'total_view_count',
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
    readonly_fields = ['user_watch_summary']
    ordering = ['-date_joined']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            annotated_movies_count=Count('watch_history__movies', distinct=True),
            annotated_series_count=Count('watch_history__series', distinct=True),
            annotated_total_views=Count('watch_history__movies', distinct=True) + Count('watch_history__series', distinct=True)
        )

    @admin.display(description='Watched Movies', ordering='annotated_movies_count')
    def watched_movies_count(self, obj):
        if hasattr(obj, 'annotated_movies_count'):
            return obj.annotated_movies_count
        if hasattr(obj, 'watch_history') and obj.watch_history:
            return obj.watch_history.movies.count()
        return 0

    @admin.display(description='Watched Series', ordering='annotated_series_count')
    def watched_series_count(self, obj):
        if hasattr(obj, 'annotated_series_count'):
            return obj.annotated_series_count
        if hasattr(obj, 'watch_history') and obj.watch_history:
            return obj.watch_history.series.count()
        return 0

    @admin.display(description='Total Views', ordering='annotated_total_views')
    def total_view_count(self, obj):
        if hasattr(obj, 'annotated_total_views'):
            return obj.annotated_total_views
        return self.watched_movies_count(obj) + self.watched_series_count(obj)

    @admin.display(description='Watch Summary')
    def user_watch_summary(self, obj):
        m_count = obj.watch_history.movies.count() if hasattr(obj, 'watch_history') and obj.watch_history else 0
        s_count = obj.watch_history.series.count() if hasattr(obj, 'watch_history') and obj.watch_history else 0
        return f"{m_count} Movies watched, {s_count} Series watched (Total: {m_count + s_count} views)"

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
        (_('Watch Statistics'), {
            'fields': ('user_watch_summary',)
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