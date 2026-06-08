from threading import Thread

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers

from rest_framework import serializers
from django.contrib.auth import get_user_model


UserModel = get_user_model()

MSG = """
Hello,

Welcome to Nuweli 🎬

Please use the verification code below to confirm your account:

{otp}

This code is valid for a limited time.  
For your security, do not share this code with anyone.

If you did not request this verification, please ignore this email.

Thank you,  
The Nuweli Team

"""


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class CustomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            'full_name',
            'profile_image',
        ]
        # read_only_fields = ['email', 'username', 'otp', 'is_superuser', 'is_staff', 'date_joined']

    def get_full_name(self, obj):
        return obj.first_name + ' ' + obj.last_name


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            'email', 'password', 'first_name',
            'country', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        user = UserModel(email=email)
        user.set_password(password)

        # BLOCK: USER ACTIVATION THROUGH EMAIL. COMMENT IT FOR EASE OF DEVELOPMENT

        user.is_active = False
        user.save()

        Thread(
            target=send_mail,
            kwargs={
                'subject': 'Account Verification Code',
                'message': MSG.format(otp=user.otp),
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'recipient_list': [email],
            }
        ).start()
        return user


class AccountActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            "first_name", "last_name",
            "date_of_birth",
            "gender",
            "email",
            "profile_image",
            "phone"
        ]


