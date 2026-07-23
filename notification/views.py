from django.shortcuts import render

from rest_framework.decorators import (
    api_view, permission_classes
)

from rest_framework import serializers

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema


class DeviceTokenRegisterRequest(serializers.Serializer):
    device_token = serializers.CharField()


@extend_schema(request=DeviceTokenRegisterRequest)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    device_token = request.data.get('device_token')
    if not device_token:
        print("invalid token",device_token, device_token=="")
        raise ValidationError({
            "error": "'device_token' is required"
        })

    print("LOGGIN ", device_token)
    request.user.device_token = device_token
    request.user.save()
    return Response({
        "success": True
    })


# @extend_schema(request=DeviceTokenRegisterRequest)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unregister_device_token(request):
    request.user.device_token = ""
    request.user.save()
    return Response({
        "success": True
    })


from .models import Device

class DeviceRegisterSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=255)
    push_token = serializers.CharField()
    platform = serializers.CharField(max_length=50)
    model = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    os_version = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    app_version = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")


@extend_schema(request=DeviceRegisterSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device(request):
    serializer = DeviceRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    device_id = serializer.validated_data['device_id']
    push_token = serializer.validated_data['push_token']
    platform = serializer.validated_data['platform']
    model = serializer.validated_data.get('model', '')
    os_version = serializer.validated_data.get('os_version', '')
    app_version = serializer.validated_data.get('app_version', '')

    device, created = Device.objects.update_or_create(
        device_id=device_id,
        defaults={
            'user': request.user,
            'push_token': push_token,
            'platform': platform,
            'model': model,
            'os_version': os_version,
            'app_version': app_version,
        }
    )

    # Sync the device token to the CustomUser model for compatibility with existing code
    request.user.device_token = push_token
    request.user.save()

    return Response({
        "success": True,
        "message": "Device registered successfully",
        "device_id": device.device_id
    })

