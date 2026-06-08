import random
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


def get_active_refresh_tokens(user):
    active_tokens = OutstandingToken.objects.filter(user=user).exclude(
        id__in=BlacklistedToken.objects.values_list("token_id", flat=True)
    ).count()
    return active_tokens


def create_otp(length:int=4):
    return ''.join(random.choices('0123456789', k=length))

