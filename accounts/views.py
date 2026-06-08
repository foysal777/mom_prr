import datetime
from threading import Thread
import logging

import jwt
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework.generics import get_object_or_404, CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import ExpiredTokenError

logger = logging.getLogger(__name__)

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenBlacklistView


from django.contrib.auth import authenticate, get_user_model
from django.core.mail import EmailMessage, send_mail
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenViewBase

# from MyPerfectLife.utils import send_email
# from stripe_payment.permissions import IsSubscribed
from .models import HelpSupport, SiteConfig
from .serializers import (
    PasswordChangeSerializer,
    CustomUserSerializer,
    UserRegisterSerializer,
    AccountActivationSerializer,
    ProfileSerializer,
)
from .request_serializers import (
    SupportQuerySerializer,
    GoogleLoginSerializer,
    AppleLoginSerializer,
    TokenLoginRequest
)

from .utils import create_otp, get_active_refresh_tokens

from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

UserModel = get_user_model()


class CustomLoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = UserModel.objects.get(email=email)
            user.save()
        except UserModel.DoesNotExist:
            raise AuthenticationFailed("No user with this email found.")

        if False and get_active_refresh_tokens(user) > 2:
            raise AuthenticationFailed("You can only use atmost two device")
        if not user.check_password(password):
            raise AuthenticationFailed("Incorrect password.")

        return super().validate(attrs)


class CustomLoginView(TokenViewBase):
    serializer_class = CustomLoginSerializer


GOOGLE_LOGIN_SECRET = settings.GOOGLE_LOGIN_SECRET


@extend_schema(request=GoogleLoginSerializer)
@api_view(['post'])
def google_login_view(request):
    logger.error(f"🔴 GOOGLE LOGIN REQUEST DATA: {request.data}")
    logger.error(f"🔴 CONTENT TYPE: {request.content_type}")
    logger.error(f"🔴 REQUEST HEADERS: {dict(request.headers)}")
    
    email = request.data.get('email')
    device_token = request.data.get('device_token')
    google_login_secret = request.data.get('google_login_secret')
    id_token = request.data.get('id_token')
    
    logger.error(f"🔴 Extracted - Email: {email}, Secret: {google_login_secret}, Device Token: {device_token}")

    if not email:
        logger.error(f"🔴 ERROR: 'email' is required. Received data: {request.data}")
        raise ValidationError({"error": "'email' is required"})

    if not google_login_secret:
        logger.error(f"🔴 ERROR: 'google_login_secret' is required. Received data: {request.data}")
        raise ValidationError({"error": "'google_login_secret' is required"})

    if google_login_secret != GOOGLE_LOGIN_SECRET:
        logger.error(f"🔴 ERROR: Invalid login secret. Expected: {GOOGLE_LOGIN_SECRET}, Got: {google_login_secret}")
        raise ValidationError({"error": "invalid login secret"})
    
    # Check if user exists, if not create them
    logger.error(f"🔴 Looking for user with email: {email}")
    user, created = UserModel.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],  # Use email prefix as username
            'is_active': True,
        }
    )
    
    if created:
        logger.error(f"✅ NEW USER CREATED: {user.id} - {user.email}")
    else:
        logger.error(f"✅ EXISTING USER FOUND: {user.id} - {user.email}")

    # Save device token if provided
    if device_token:
        user.device_token = device_token
        user.save()
        logger.error(f"✅ Device token saved for user: {user.email}")

    refresh = RefreshToken.for_user(user)
    logger.error(f"✅ Tokens generated successfully for user: {user.email}")

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'is_new_user': created,  # Tell client if this is a new registration
    })


APPLE_LOGIN_SECRET = settings.APPLE_LOGIN_SECRET


@extend_schema(request=GoogleLoginSerializer)
@api_view(['post'])
def apple_login_view(request):
    logger.error(f"🍎 APPLE LOGIN REQUEST DATA: {request.data}")
    logger.error(f"🍎 CONTENT TYPE: {request.content_type}")
    logger.error(f"🍎 REQUEST HEADERS: {dict(request.headers)}")
    
    email = request.data.get('email')
    device_token = request.data.get('device_token')
    apple_login_secret = request.data.get('apple_login_secret')
    id_token = request.data.get('id_token')
    user_data = request.data.get('user')  # Apple sends user info separately
    
    logger.error(f"🍎 Extracted - Email: {email}, Secret: {apple_login_secret}, Device Token: {device_token}")

    if not email:
        logger.error(f"🍎 ERROR: 'email' is required. Received data: {request.data}")
        raise ValidationError({"error": "'email' is required"})

    if not apple_login_secret:
        logger.error(f"🍎 ERROR: 'apple_login_secret' is required. Received data: {request.data}")
        raise ValidationError({"error": "'apple_login_secret' is required"})

    if apple_login_secret != APPLE_LOGIN_SECRET:
        logger.error(f"🍎 ERROR: Invalid login secret. Expected: {APPLE_LOGIN_SECRET}, Got: {apple_login_secret}")
        raise ValidationError({"error": "invalid login secret"})
    
    # Check if user exists, if not create them
    logger.error(f"🍎 Looking for user with email: {email}")
    user, created = UserModel.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],  # Use email prefix as username
            'is_active': True,
        }
    )
    
    if created:
        logger.error(f"✅ NEW APPLE USER CREATED: {user.id} - {user.email}")
        # If user data provided, update full name
        if user_data:
            full_name = user_data.get('name')
            if full_name:
                user.full_name = full_name
                user.save()
                logger.error(f"✅ Full name saved: {full_name}")
    else:
        logger.error(f"✅ EXISTING APPLE USER FOUND: {user.id} - {user.email}")

    # Save device token if provided
    if device_token:
        user.device_token = device_token
        user.save()
        logger.error(f"✅ Device token saved for user: {user.email}")

    refresh = RefreshToken.for_user(user)
    logger.error(f"✅ Tokens generated successfully for Apple user: {user.email}")

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'is_new_user': created,  # Tell client if this is a new registration
    })


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({"detail": "Refresh token is missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)

            user = token.get('user_id', None)

            if not user:
                raise ValidationError({
                    "error": "token does'nt contain user info"
                })

            # Try to get the user from the database (optional, since token contains 'user_id')
            # This is an additional safeguard in case the token was tampered with.
            user_model = UserModel
            if not user_model.objects.filter(id=user).exists():
                raise ValidationError({
                    "error": "user does'nt exists"
                })

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return super().post(request, *args, **kwargs)


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = (AllowAny,)
    queryset = UserModel.objects.all()


@extend_schema(
    request=PasswordChangeSerializer,
    responses={
        200: {
            "example": {
                "success": True,
                "message": "password changed successfully"
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password')
    if not old_password and request.user.has_usable_password():
        return Response(data={
            "error": "'old_password' is required"
        })
    if not request.user.check_password(old_password):
        return Response(data={
            "Error": "The old password is incorrect."
        }, status=status.HTTP_400_BAD_REQUEST)

    password = request.data.get('password')
    if not password:
        return Response(data={
            "error": "'password' is required"
        })

    request.user.set_password(password)
    request.user.save()
    return Response(data={
        "success": True,
        "message": "Password changed successfully."
    }, status=status.HTTP_200_OK)


@extend_schema(
    request={
        'application/json': {
            'example': {
                'email': 'example@gmail.com',
            },
        }
    },
    responses={
        200: {'example':{
            "success": True,
            "message": "an otp is sent to example@gmail.com "
        }}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    email_subject = "Password Reset Request"

    if not email:
        return Response(data={
            "error": "'email' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(UserModel, email=email)
    user.otp = create_otp()
    email_body = f"""
        Hello,

        We received a request to reset the password for your Nuweli account.

        Please use the verification code below to reset your password:

        {user.otp}

        This code is valid for a limited time.
        For your security, do not share this code with anyone.

        If you did not request a password reset, please ignore this email.

        Thank you,
        The Nuweli Team
    """
    print(f"email: {email}. otp: {user.otp}")
    Thread(
        target=send_mail,
        kwargs={
            "subject": email_subject,
            "message": f"your password reset otp: {user.otp}",
            "html_message": email_body,
            "from_email": settings.EMAIL_HOST_USER,
            "recipient_list": [email],
            "fail_silently": False,
        }
    ).start()

    user.save()
    return Response(data={
        "success": True,
        "message": f"an otp is sent to {email}"
    })


@extend_schema(
    request={
        'application/json': {
            'example': {
                'email': 'abc@example.com',
                'otp': '4232',
                'action': 'password_reset/activate_account'
            }
        }
    },
    responses={
        200: {'example': {
            "success": True,
            "message": "otp is correct"
        }}
    }
)
@api_view(['post'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    action = request.data.get('action')

    # if not action:
    #     action = 'password_reset'

    if action not in (ac_li := ['password_reset', 'activate_account']):
        raise ValidationError({"error": f"action can be one of {ac_li}"})
    if not email:
        return Response(data={
            "error": "'email' is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    if not otp:
        return Response(data={
            "error": "'otp' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(UserModel, email=email)
    if user.otp != otp:
        user.save()
        return Response(data={
            "error": "The OTP is incorrect."
        }, status=status.HTTP_400_BAD_REQUEST)

    user.otp = create_otp()
    user.save()

    return Response(data={
        "success": True,
        "action_token": jwt.encode(
            payload={
                "user_id": user.id,
                'action': action,
                'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=1)
            },
            key=settings.SECRET_KEY,
            algorithm="HS256"
        ),
        "message": "Otp is Correct"
    })


@extend_schema(
    request={
        'application/json': {
            'example': {
                'email': 'abc@example.com',
                'action_token': 'asd.bds.dfs',
                'new_password': 'string',
            }
        }
    },
    responses={
        200: {'example': {
            "success": True,
            "message": "Password changed successfully."
        }}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    action_token = request.data.get('action_token')
    new_password = request.data.get('new_password')

    if not action_token:
        return Response(data={
            "error": "'action_token' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    if not new_password:
        return Response(data={
            "error": "'new_password' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        payload = jwt.decode(action_token, settings.SECRET_KEY,
                             algorithms=["HS256"])
        if 'user_id' not in payload or 'action' not in payload or \
                payload['action'] != 'password_reset':
            raise ValidationError({"error": "invalid token for password reset."})
        user = get_object_or_404(UserModel, id=payload['user_id'])

    except jwt.ExpiredSignatureError as e:
        raise ValidationError({"error": "token expired"})

    except jwt.InvalidTokenError as e:
        raise ValidationError({"error": "invalid token"})

    except jwt.PyJWTError as e:
        raise ValidationError({"error": "token validation failed"})

    if user.check_password(new_password):
        return Response(data={
                "error": "You can not use the old password."
            }, status=status.HTTP_400_BAD_REQUEST
        )
    # if user.otp != otp:
    #     raise ValidationError({"error": "invalid otp"})

    user.set_password(new_password)
    user.otp = create_otp()
    user.save()
    return Response(data={
        "success": True,
        "message": "Password changed successfully."
    })


class ProfileUpdateView(RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ('get', 'patch',)
    # parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user


class ActivateAccountView(CreateAPIView):
    serializer_class = AccountActivationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = get_object_or_404(UserModel, email=email, )
        print(user)
        print(user.otp, user.otp.__class__)
        print(otp, otp.__class__)
        if user.otp != otp:
            raise ValidationError({"error": "The OTP is incorrect."})
        user.otp = create_otp()
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)

        return Response(data={
            "success": True,
            "message": "account activated",
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })


@api_view(['POST'])
def resend_otp(request, email):
    if not email:
        return Response(data={
            "error": "'email' is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(UserModel, email=email)

    user.otp = create_otp()

    user.save()

    email_subject = "Password Reset Request"

    # user.otp = create_otp()
    email_body = f"""
    <html>
        <head></head>
        <body>
            <h3>Use this otp: <span style="text-color:yellow">{user.otp}</span>
        </body>
    </html>
    """
    Thread(
        target=send_mail,
        kwargs={
            "subject": email_subject,
            "message": f"your password reset otp: {user.otp}",
            "html_message": email_body,
            "from_email": settings.EMAIL_HOST_USER,
            "recipient_list": [email],
            "fail_silently": False,
        }
    ).start()

    return Response({
        "data": {
            "msg": "resend otp is sent."
        }
    })


class ProfileAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    allowed_methods = ['get', 'patch']

    def get_object(self):
        print("|DEBUG .......")
        # print(self.request.user.full_name.__class__)
        return self.request.user


@extend_schema(request=SupportQuerySerializer)
@api_view(["POST"])
def create_support_query(reqeust):
    req_ser = SupportQuerySerializer(data=reqeust.data)
    req_ser.is_valid(raise_exception=True)
    HelpSupport.objects.create(
        email=req_ser.validated_data['email'],
        description=req_ser.validated_data['description']
    )
    return Response({
        "message": "you query will be responsed soon."
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(reqeust):
    reqeust.user.delete()
    return Response({
        "message": "account deleted"
    })



@api_view(["post"])
@permission_classes([IsAuthenticated])
def change_language(request, language):
    # language = request.data['language']
    if language not in ['en_US', 'fr_FR', 'es_ES']:
        raise ValidationError({"error": f"language must be one of {['en_US', 'fr_FR', 'es_ES']}"})

    request.user.language=language
    request.user.save()
    return Response({
        "message": "language updated"
    })


@api_view(['get'])
def get_privacy_policy(request):
    site_config = SiteConfig.objects.first()
    return Response({
        "privacy_policy": site_config.privacy_policy if site_config else ""
    })


@api_view(['post'])
@permission_classes([IsAuthenticated])
def get_login_token(request):
    
    return Response({
        "token": jwt.encode({"user_id": request.user.id}, key=settings.SECRET_KEY, algorithm="HS256")
    })


@extend_schema(request=TokenLoginRequest)
@api_view(['post'])
def token_login(request):
    if 'token' not in request.data:
        raise ValidationError({"error": "token is required"})

    token = request.data['token']
    try:
        payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        raise ValidationError({"error": str(e)})

    user_id = int(payload['user_id'])

    user = get_object_or_404(UserModel, id=user_id)

    refresh_token = RefreshToken.for_user(user)
    
    from .serializers import ProfileSerializer
    user_data = ProfileSerializer(user, context={'request': request}).data
    
    return Response({
        "access": str(refresh_token.access_token),
        "refresh": str(refresh_token),
        "user": user_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription_status(request):
    user = request.user
    subscription = getattr(user, 'subscription', None)

    if subscription is None:
        return Response({
            "is_subscribed": False,
            "message": "No subscription found.",
            "subscribe_till": None,
            "period": None,
        })

    is_active = subscription.remaining_time.total_seconds() > 0

    return Response({
        "is_subscribed": is_active,
        "message": "Active subscription." if is_active else "Subscription has expired.",
        "subscribe_till": subscription.subscribe_till,
        "period": subscription.period,
    })