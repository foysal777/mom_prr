import stripe
import os

from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from movie_series.models import (
    Movie, Series, PremiumCollection
)

from .models import Subscription


UserModel = get_user_model()


def create_stripe_subscription_checkout_url(
    price_id: str,
    metadata: dict,
    success_url: str = None,
    cancel_url: str = None
) -> str:

    if not stripe.api_key:
        raise ValidationError(
            "Stripe API key is not set."
            "Please configure it."
        )

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=success_url if success_url else "example.com",
            cancel_url=cancel_url if cancel_url else "example.com/?error=sdfa",
            metadata=metadata,
        )
        return checkout_session.url
    except stripe.error.StripeError as e:
        raise ValidationError(f"Stripe Error: {e.user_message or e.code}")
    except Exception as e:
        # Catch any other unexpected errors
        raise ValidationError(f"An unexpected error occurred: {str(e)}")


def create_payment_url(amount_usd, metadata, success_url, cancel_url):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Payment',
                },
                'unit_amount': int(amount_usd * 100),  # Convert to cents
            },
            'quantity': 1,
        }],
        metadata=metadata,
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def handle_movie_series_purchase(metadata):
    user_id = metadata['user_id']
    movie_ids = eval(metadata['movie_ids'])
    series_ids = eval(metadata['series_ids'])

    premium_collection, _created = PremiumCollection.objects.get_or_create(
        user_id=user_id
    )
    premium_collection.movies.add(*movie_ids)
    premium_collection.series.add(*series_ids)
    return Response({"message": "successfully added to premium_collection"})


def handle_checkout_session_complete(event):
    metadata = event['data']['object']['metadata']
    user_id = metadata.get('user_id')
    # subscription_type = metadata.get('subscription_type')
    plan_id = metadata.get('plan_id')

    app_name = metadata.get('app_name')

    if app_name != "mom_pr":
        raise ValidationError({"error": "You have lost home."})

    stripe_subscription_id = event['data']['object']['subscription']
    print("DEBUGINH SUB ID....")
    if stripe_subscription_id:
        sub, _created = Subscription.objects.get_or_create(user_id=user_id)

        if sub.stripe_subscription_id:
            try:
                stripe.Subscription.cancel(sub.stripe_subscription_id)
            except stripe._error.StripeError as e:
                pass
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            metadata=metadata,
        )
        print("subscription_modified....")

        period = metadata['period']
        sub.set_subscribe(period)
        sub.stripe_subscription_id = stripe_subscription_id
        sub.save()
    else:
        return handle_movie_series_purchase(metadata)

    print("save return response")
    return Response({'success': True}, status=200)


def handle_subscription_period_complete(metadata):
    print(metadata)
    user_id = metadata.get('user_id')

    period = metadata['period']
    # subscription_type = metadata.get('subscription_type')

    app_name = metadata.get('app_name')

    if app_name != "mom_pr":
        raise ValidationError({"error": "You have lost home."})

    sub = get_object_or_404(Subscription, user_id=user_id)

    sub.set_subscribe(period)
    # sub.set_subscribe(subscription_type)

    sub.save()

    print("save return response")
    return Response({'success': True}, status=200)



