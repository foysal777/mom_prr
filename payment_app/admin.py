import datetime
from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'period',
        'amount',
        'purchase_date',
        'subscribe_till',
        'is_active',
        'remaining_time_display',
        'stripe_subscription_id'
    ]
    list_filter = [
        'period',
        'purchase_date',
        'subscribe_till'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'user__full_name',
        'stripe_subscription_id'
    ]
    readonly_fields = [
        'purchase_date',
        'remaining_time_display'
    ]
    ordering = ['-purchase_date']

    def has_add_permission(self, request):
        return False

    @admin.display(description='Active', boolean=True)
    def is_active(self, obj):
        if not obj.subscribe_till:
            return False
        return obj.subscribe_till > datetime.datetime.now(datetime.timezone.utc)

    @admin.display(description='Remaining Time')
    def remaining_time_display(self, obj):
        rem = obj.remaining_time
        if not rem or rem.total_seconds() <= 0:
            return "Expired"
        days = rem.days
        hours = rem.seconds // 3600
        return f"{days}d {hours}h"
