from django.urls import path

from .views import register_device_token, unregister_device_token

urlpatterns = [
    path("register_device_token/", register_device_token),
    path("unregister_device_token/", unregister_device_token),
]