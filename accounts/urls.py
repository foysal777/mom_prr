from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenBlacklistView


from accounts.views import (
    # ProfileUpdateView,
    UserCreateAPIView,
    CustomLoginView,
    get_login_token,
    request_password_reset,
    token_login,
    verify_otp,
    change_password,
    reset_password,
    ActivateAccountView,
    resend_otp,
    ProfileAPIView,
    create_support_query,
    delete_account,
    CustomTokenRefreshView,
    google_login_view,
    apple_login_view,
    get_privacy_policy,
    change_language,
    check_subscription_status,
)

urlpatterns = [
    path('register/', UserCreateAPIView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('google_login/', google_login_view, name='google_login'),
    path('apple_login/', apple_login_view, name='apple_login'),
    path('logout/', TokenBlacklistView.as_view(), name='login'),
    path('delete/', delete_account, name='delete-account'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('refresh_token/', CustomTokenRefreshView.as_view(), name='token_verify'),
    # path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('request_password_reset/', request_password_reset),
    path('verify_otp/', verify_otp),
    path('change_password', change_password),
    path('reset_password/', reset_password),
    path('<str:email>/resend_otp/', resend_otp),
    path('profile/', ProfileAPIView.as_view()),
    path('subscription_status/', check_subscription_status),
    path('help_support/', create_support_query),
    path('privacy_policy/', get_privacy_policy),
    path('change_language/<str:language>/', change_language),

    path('get_login_token/', get_login_token),
    path('token_login/', token_login),
]
