from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

