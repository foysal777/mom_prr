from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Subscription

UserModel = get_user_model()


@receiver(post_save, sender=UserModel)
def create_default_subscription(sender, instance, created, **kwargs):
    if not hasattr(instance, "subscription"):
        print("create subscription signal")
        Subscription.objects.create(user=instance)
        print(instance.subscription)
