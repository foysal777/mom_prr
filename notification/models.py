from django.db import models
from django.conf import settings

# Create your models here.

class Device(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
        blank=True
    )
    device_id = models.CharField(max_length=255, unique=True)
    push_token = models.TextField()
    platform = models.CharField(max_length=50)  # 'android', 'ios', etc.
    model = models.CharField(max_length=255, default="", blank=True)
    os_version = models.CharField(max_length=50, default="", blank=True)
    app_version = models.CharField(max_length=50, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_email = self.user.email if self.user else "Anonymous"
        return f"{user_email} - {self.model or self.platform} ({self.device_id})"
