from rest_framework import serializers


class SupportQuerySerializer(serializers.Serializer):
    email = serializers.EmailField()
    description = serializers.CharField()
    pass

class GoogleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    google_login_secret = serializers.CharField()
    id_token = serializers.CharField(required=False)


class AppleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    apple_login_secret = serializers.CharField()
    id_token = serializers.CharField(required=False)
    user = serializers.JSONField(required=False)  # Apple sends user info as JSON


class GuestLoginSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    push_token = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    os_version = serializers.CharField(required=False, allow_blank=True)
    app_version = serializers.CharField(required=False, allow_blank=True)


class TokenLoginRequest(serializers.Serializer):
    token = serializers.CharField()
