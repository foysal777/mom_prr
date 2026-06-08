from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from django.contrib.auth import get_user_model

from .models import (
    Movie, Episode, WatchHistory, WatchLater,
    PremiumCollection, Like, DisLike, Season
)
from movie_series.vdocipher_client import VdocipherClient
from notification.utils import send_fcm_notification
import json

UserModel = get_user_model()

client = VdocipherClient()


@receiver(post_delete, sender=Movie)
@receiver(post_delete, sender=Episode)
def delete_related_video_file_from_vdocipher(
    sender, instance, **kwargs
):
    if instance.file_uuid:
        client.delete_videos([instance.file_uuid])


@receiver(post_save, sender=Season)
@receiver(post_save, sender=Movie)
def post_save_handle(
    sender, instance, **kwargs
):
    if not (instance.publish and instance.notifyees):
        print("RETURNING.....")
        return

    for user in UserModel.objects.filter(id__in=instance.notifyees):
        if user.device_token:
            alias_type = "movie" if isinstance(instance, Movie) else "season"
            send_fcm_notification(
                user.device_token,
                "Reminder Published",
                json.dumps({
                    "id": instance.id,
                    "type": alias_type,
                    "msg": f"The {alias_type}: {instance.get_name()} is published"
                })
            )
    instance.notifyees=[]
    instance.save()
    pass


@receiver(post_save, sender=UserModel)
def new_user_preparing(
    sender, instance, created, **kwargs
):
    if created:
        WatchHistory.objects.create(user=instance)
        WatchLater.objects.create(user=instance)
        PremiumCollection.objects.create(user=instance)
        Like.objects.create(user=instance)
        DisLike.objects.create(user=instance)
