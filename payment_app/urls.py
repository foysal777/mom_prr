from django.urls import path
from .views import (
    stripe_webhook,
    subscribe,
    purchage_movie_series,
    profile, moncash_webhook,
    moncash_success_view, moncash_cancel_view,
    subscription_prices, cancel_subscription,
    revenuecat_sync_purchase, revenuecat_webhook
)


urlpatterns = [
    path('listen_events/', stripe_webhook),
    path('listen_moncash_events/', moncash_webhook),
    path('moncash_success/', moncash_success_view),
    path('moncash_cancel/', moncash_cancel_view),
    path('subscribe/', subscribe),
    path('cancel_subscription/', cancel_subscription),
    path('purchase/', purchage_movie_series),
    path('profile/', profile),
    path('subcription_prices/', subscription_prices),
    path('revenuecat_sync/', revenuecat_sync_purchase),
    path('revenuecat_webhook/', revenuecat_webhook),
]


