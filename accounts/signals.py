from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from django.contrib.auth import get_user_model
from django.conf import settings
from threading import Thread
from django.core.mail import EmailMessage, send_mail


from .models import HelpSupport, SiteConfig


UserModel = get_user_model()


@receiver(post_save, sender=HelpSupport)
def handle_query_answer(
    sender, instance, created, **kwargs
):
    if instance.is_solved and instance.answer:
        Thread(
            target=send_mail,
            kwargs={
                "subject": "Response for you query.",
                "message": instance.answer,
                "html_message": instance.answer,
                "from_email": settings.EMAIL_HOST_USER,
                "recipient_list": [instance.email],
                "fail_silently": True,
            }
        ).start()
        # instance.delete()


@receiver(post_save, sender=SiteConfig)
def handle_site_config_update(
    sender, instance, created, **kwargs
):
    settings.SITE_CONFIG = instance