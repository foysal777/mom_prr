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
