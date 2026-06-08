from django.apps import AppConfig
from django.conf import settings

from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from . import signals

        print("preparing app")
        from .models import SiteConfig
        print("\n\n........ setting up SiteConfig in app.ready ..........\n\n")
        settings.SITE_CONFIG = SiteConfig.objects.first()

