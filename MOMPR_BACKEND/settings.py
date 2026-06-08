

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import redis
import stripe

load_dotenv()

VDOCIPHER_WEBHOOK_SECRET = os.environ['VDOCIPHER_WEBHOOK_SECRET']

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-lczs&=_8cm9(p_rvzk^4!rh7wfgep-j^q+nix(r@@w)@e*+@%*'
GOOGLE_LOGIN_SECRET = "^sa@!24l425$fZa#32f|$"
APPLE_LOGIN_SECRET = "^apple@!24l425$fZa#32f|$"
DEBUG = True

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://fawn-moved-yearly.ngrok-free.app",
    "https://personally-liberal-scorpion.ngrok-free.app",
    "http://172.252.13.73",
    "https://admin.nuweli.com",
    "https://jocular-pixie-65a2b9.netlify.app"
]

# USE_X_FORWARDED_HOST = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

stripe.api_key = os.environ['STRIPE_SECRET_KEY']
REDIS_CLIENT = redis.Redis()
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PATCH', 'DELETE']
CORS_ALLOW_HEADERS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'django_cleanup.apps.CleanupConfig',
    'django_filters',
    'accounts',
    'movie_series',
    'payment_app',
    'notification'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MOMPR_BACKEND.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'MOMPR_BACKEND.wsgi.application'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = "no_reply@nuweli.com"
EMAIL_HOST_PASSWORD = "bpru wksa kcce plpq"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=1222222),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=777),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'Mom_PR',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'COMPONENT_SPLIT_REQUEST': True,
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular.generators.SchemaGenerator',
    'SCHEMA_PATH_PREFIX': '/api/',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'SERVE_INCLUDE_SCHEMA': False,
}


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static_root'
STATICFILES_DIRS = [
    BASE_DIR/'static_files'
]

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
