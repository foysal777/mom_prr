import os
import json

from decimal import Decimal
import stripe

from django.shortcuts import render
from django.conf import settings

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema
import uuid

from .stripe_utils import (
    create_stripe_subscription_checkout_url,
    handle_checkout_session_complete,
    handle_subscription_period_complete,
    handle_invoice_payment_succeeded,
    handle_movie_series_purchase,
    create_payment_url
)

from .serializers import (
    SubscriptionRequestSerializer,
    MovieSeriesPurchaseRequestSerializer,
    RevenueCatSyncSerializer
)
from .models import Subscription

from movie_series.models import Movie, Series, PremiumCollection
from .moncash_client import MoncashClient
from accounts.models import SiteConfig


from django.contrib.auth import get_user_model
UserModel = get_user_model()

moncash_client = MoncashClient()


@extend_schema(exclude=True)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('stripe-signature') or request.META.get('HTTP_STRIPE_SIGNATURE')
    if not sig_header:
        return Response({"error": "validation signature not found"}, status=status.HTTP_400_BAD_REQUEST)

    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    if not webhook_secret:
        return Response({"error": "STRIPE_WEBHOOK_SECRET is not set in environment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret,
        )
        print("Received Stripe webhook event:", event.get('type'))
    except ValueError as e:
        return Response({'error': "invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        return Response({'error': "invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    event_type = event.get('type')
    if event_type == 'checkout.session.completed':
        return handle_checkout_session_complete(event)

    if event_type == 'invoice.payment_succeeded':
        return handle_invoice_payment_succeeded(event)

    # For any other unhandled Stripe events, return HTTP 200 OK so Stripe knows it was received and does not retry
    return Response({'status': 'ignored', 'event_type': event_type}, status=status.HTTP_200_OK)


@extend_schema(exclude=True)
@api_view(['GET', 'POST'])
def moncash_webhook(request):
    transaction_id = request.query_params.get('transactionId')
    print("MONCASH WEBHOOK")
    print("transaction_id: ", transaction_id)

    response, _err = moncash_client.retrieve_transaction(
        transaction_id
    )

    if _err:
        raise ValidationError({"error": _err})

    order_id = response['payment']['reference']

    metadata = json.loads(order_id)
    if metadata['app_name'] != 'mom_pr':
        raise ValidationError({
            "error": "You've lost home."
        })
    if metadata.get('mode', '') == 'purchase':
        return handle_movie_series_purchase(metadata)

    # 'period' is only given for subscription mode
    period = metadata['period']
    user_id = metadata['user_id']
    sub, _created = Subscription.objects.get_or_create(user_id=user_id)
    sub.set_subscribe(period)
    sub.save()
    return Response({
        "msg": "the subscription increased"
    })


@extend_schema(exclude=True)
@api_view(['GET', 'POST'])
def moncash_success_view(request):

    return Response({
        "success": True
    })


@extend_schema(exclude=True)
@api_view(['GET', 'POST'])
def moncash_cancel_view(request):
    print("CANCEL URL CALLED")
    return Response({
        "success": True
    })


# @extend_schema(request=SubscriptionRequestSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    stripe_subscription_id = request.user.subscription.stripe_subscription_id

    if stripe_subscription_id:
        stripe.Subscription.cancel(stripe_subscription_id)
    request.user.subscription.stripe_subscription_id = ""
    request.user.subscription.subscribe_till = None
    request.user.subscription.period = None

    request.user.subscription.save()
    return Response({"success": True})


@extend_schema(request=SubscriptionRequestSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe(request):
    req_ser = SubscriptionRequestSerializer(data=request.data)
    req_ser.is_valid(raise_exception=True)
    period = req_ser.validated_data['period']

    metadata = {
        "app_name": "mom_pr",
        "user_id": request.user.id,
        "period": period
    }

    site_config = SiteConfig.objects.first()
    if not site_config:
        return Response({"error": "Subscription service is not configured"}, status=503)

    if req_ser.validated_data.get('is_moncash'):
        if period == 'yearly':
            amount = site_config.yearly_moncash_subscription_price
        else:
            amount = site_config.moncash_subscription_price

        if not amount or amount <= 0:
            return Response({"error": f"{period} Moncash subscription is not configured"}, status=503)

        metadata['randomness'] = str(uuid.uuid4())
        url, _err = moncash_client.create_payment(
            amount, json.dumps(metadata)
        )
        if _err:
            raise ValidationError({
                "error": _err
            })

        return Response({
            "url": url
        })

    if period == 'monthly' and not site_config.subscription_price_id:
        return Response({"error": "monthly subscription is not enabled"}, status=503)

    if period == 'yearly' and not site_config.yearly_subscription_price_id:
        return Response({"error": "yearly subscription is not enabled"}, status=503)

    price_id = (
        site_config.subscription_price_id
        if period == 'monthly' else site_config.yearly_subscription_price_id
    )

    url = create_stripe_subscription_checkout_url(
        price_id=price_id,
        metadata=metadata,
        success_url="https://example.com",
        cancel_url="https://example.com?error=abc",
    )
    return Response({
        "url": url
    })


@extend_schema(request=MovieSeriesPurchaseRequestSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchage_movie_series(request):
    req_ser = MovieSeriesPurchaseRequestSerializer(data=request.data)
    req_ser.is_valid(raise_exception=True)
    movie_ids = [movie.id for movie in movie_set]\
        if (movie_set := req_ser.validated_data.get('movie_set')) else []

    series_ids = [series.id for series in series_set]\
        if (series_set := req_ser.validated_data.get('series_set')) else []

    is_moncash = req_ser.validated_data.get('is_moncash')
    metadata = {
        'app_name': 'mom_pr',
        'user_id': request.user.id
    }

    invalid_premium_movies = Movie.objects.filter(
        id__in=movie_ids,
        premiumcollection__user=request.user
    ).values_list('id', flat=True)

    if invalid_premium_movies:
        raise ValidationError({
            "error": "some of the movies are already"
                     f" in you premium collection"
        })

    invalid_premium_series = Series.objects.filter(
        id__in=series_ids,
        premiumcollection__user=request.user
    ).values_list('id', flat=True)

    if invalid_premium_series:
        raise ValidationError({
            "error": f"some of the series are already"
                     " in you premium collection {invalid_premium_movies}"
        })

    net_price = Decimal(0.0)
    is_moncash = req_ser.validated_data.get('is_moncash')
    if 'movie_set' in req_ser.validated_data.keys():
        for movie in req_ser.validated_data['movie_set']:
            net_price += movie.premium_price_gourde\
                if is_moncash else movie.premium_price_usd

    if 'series_set' in req_ser.validated_data.keys():
        for series in req_ser.validated_data['series_set']:
            net_price += series.premium_price_gourde\
                if is_moncash else series.premium_price_usd

    # assert isinstance(, class_or_tuple)
    metadata['movie_ids'] = str(movie_ids)\
        if movie_ids else str([])

    metadata['series_ids'] = str(series_ids)\
        if series_ids else str([])

    # return Response({"ntp": net_price, 'm': req_ser.validated_data['movie_set']})
    if req_ser.validated_data.get('is_moncash'):
        metadata['randomness'] = str(uuid.uuid4())
        metadata['mode'] = 'subscription'
        url, _err = moncash_client.create_payment(
            net_price, json.dumps(metadata)
        )
        if _err:
            raise ValidationError({
                "error": _err
            })

        return Response({
            "url": url
        })
        pass
    else:
        url = create_payment_url(
            net_price,
            metadata=metadata,
            success_url="https://example.com",
            cancel_url="https://example.com?error=abcd"
        )
    return Response({
        "url": url
    })


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def profile(request):
#     pass


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    print(request.user.subscription.remaining_time)
    return Response({
        "is_subscribed": bool(request.user.subscription.remaining_time),
        "period": request.user.subscription.period,
        "next_billing": (
            request.user.subscription.subscribe_till
            if request.user.subscription.subscribe_till else None
        )
    })
    pass


@api_view(['GET'])
def subscription_prices(request):
    site_config = SiteConfig.objects.first()

    stripe_price_monthly = 0.0
    stripe_price_yearly = 0.0

    if site_config and site_config.subscription_price_id:
        try:
            stripe_obj = stripe.Price.retrieve(site_config.subscription_price_id)
            if hasattr(stripe_obj, 'unit_amount') and stripe_obj.unit_amount is not None:
                stripe_price_monthly = stripe_obj.unit_amount / 100
        except Exception as e:
            print(f"Error retrieving monthly stripe price: {e}")

    if site_config and site_config.yearly_subscription_price_id:
        try:
            stripe_obj = stripe.Price.retrieve(site_config.yearly_subscription_price_id)
            if hasattr(stripe_obj, 'unit_amount') and stripe_obj.unit_amount is not None:
                stripe_price_yearly = stripe_obj.unit_amount / 100
        except Exception as e:
            print(f"Error retrieving yearly stripe price: {e}")

    moncash_monthly = float(site_config.moncash_subscription_price) if site_config and site_config.moncash_subscription_price is not None else 0.0
    moncash_yearly = float(site_config.yearly_moncash_subscription_price) if site_config and site_config.yearly_moncash_subscription_price is not None else 0.0

    return Response({
        "stripe": {
            "monthly": stripe_price_monthly,
            "yearly": stripe_price_yearly,
        },
        "moncash": {
            "monthly": moncash_monthly,
            "yearly": moncash_yearly,
        }
    })


import asyncio

async def sleep_3_sec():
    await asyncio.sleep(3)

async def sleep_5_sec():
    await asyncio.sleep(5)


async def sleep_7_sec():
    await asyncio.sleep(7)


@extend_schema(request=RevenueCatSyncSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revenuecat_sync_purchase(request):
    """
    Endpoint for frontend to sync RevenueCat purchase after successful transaction
    """
    req_ser = RevenueCatSyncSerializer(data=request.data)
    req_ser.is_valid(raise_exception=True)
    
    purchase_type = req_ser.validated_data['purchase_type']
    
    if purchase_type == 'subscription':
        period = req_ser.validated_data['period']
        sub, _created = Subscription.objects.get_or_create(user_id=request.user.id)
        sub.set_subscribe(period)
        sub.save()
        return Response({"success": True, "message": "Subscription synced successfully."})
        
    elif purchase_type == 'movie':
        movie = req_ser.validated_data['movie_id']
        premium_collection, _created = PremiumCollection.objects.get_or_create(
            user_id=request.user.id
        )
        premium_collection.movies.add(movie)
        return Response({"success": True, "message": "Movie unlocked successfully."})
        
    elif purchase_type == 'series':
        series = req_ser.validated_data['series_id']
        premium_collection, _created = PremiumCollection.objects.get_or_create(
            user_id=request.user.id
        )
        premium_collection.series.add(series)
        return Response({"success": True, "message": "Series unlocked successfully."})


@extend_schema(exclude=True)
@api_view(['POST'])
def revenuecat_webhook(request):
    """
    Webhook endpoint for RevenueCat. Configure this in RevenueCat dashboard.
    """
    event = request.data.get('event', {})
    if not event:
        return Response({"error": "Invalid payload"}, status=400)
    
    event_type = event.get('type')
    app_user_id = event.get('app_user_id')
    product_id = event.get('product_id', '')
    
    if not app_user_id:
        return Response({"error": "Missing app_user_id"}, status=400)
        
    try:
        user = UserModel.objects.get(id=app_user_id)
    except UserModel.DoesNotExist:
        # User not found, just ignore
        return Response({"success": True, "message": "User not found, ignored."})

    if event_type in ['INITIAL_PURCHASE', 'RENEWAL', 'UNCANCELLATION']:
        # Subscription purchased or renewed
        if 'month' in product_id.lower() or 'monthly' in product_id.lower():
            period = 'monthly'
        elif 'year' in product_id.lower() or 'yearly' in product_id.lower():
            period = 'yearly'
        else:
            # default to monthly if we can't determine
            period = 'monthly'
            
        sub, _created = Subscription.objects.get_or_create(user_id=user.id)
        sub.set_subscribe(period)
        sub.save()
        
    elif event_type in ['CANCELLATION', 'EXPIRATION']:
        try:
            sub = Subscription.objects.get(user_id=user.id)
            sub.subscribe_till = None
            sub.period = None
            sub.save()
        except Subscription.DoesNotExist:
            pass
            
    elif event_type == 'NON_RENEWING_PURCHASE':
        premium_collection, _created = PremiumCollection.objects.get_or_create(
            user_id=user.id
        )
        if product_id.startswith('movie_'):
            try:
                m_id = int(product_id.split('_')[1])
                premium_collection.movies.add(m_id)
            except (IndexError, ValueError):
                pass
        elif product_id.startswith('series_'):
            try:
                s_id = int(product_id.split('_')[1])
                premium_collection.series.add(s_id)
            except (IndexError, ValueError):
                pass

    return Response({"success": True})
