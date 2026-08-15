import stripe
import os
import json
import ast

from django.contrib.auth import get_user_model

from rest_framework import status
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
    user_id = metadata.get('user_id')
    if not user_id:
        return Response({"message": "No user_id found in metadata"}, status=status.HTTP_200_OK)

    movie_ids = []
    series_ids = []

    raw_movie_ids = metadata.get('movie_ids', '[]')
    if isinstance(raw_movie_ids, list):
        movie_ids = raw_movie_ids
    elif isinstance(raw_movie_ids, str):
        try:
            movie_ids = json.loads(raw_movie_ids)
        except Exception:
            try:
                movie_ids = ast.literal_eval(raw_movie_ids)
            except Exception:
                movie_ids = []

    raw_series_ids = metadata.get('series_ids', '[]')
    if isinstance(raw_series_ids, list):
        series_ids = raw_series_ids
    elif isinstance(raw_series_ids, str):
        try:
            series_ids = json.loads(raw_series_ids)
        except Exception:
            try:
                series_ids = ast.literal_eval(raw_series_ids)
            except Exception:
                series_ids = []

    premium_collection, _created = PremiumCollection.objects.get_or_create(
        user_id=user_id
    )
    if movie_ids:
        premium_collection.movies.add(*movie_ids)
    if series_ids:
        premium_collection.series.add(*series_ids)
    return Response({"message": "successfully added to premium_collection"}, status=status.HTTP_200_OK)


def handle_checkout_session_complete(event):
    session = event.get('data', {}).get('object', {})
    metadata = session.get('metadata') or {}

    app_name = metadata.get('app_name')
    if app_name != "mom_pr":
        print("checkout.session.completed ignored: app_name is not mom_pr")
        return Response({'message': "Ignored: not a mom_pr checkout session"}, status=status.HTTP_200_OK)

    user_id = metadata.get('user_id')
    if not user_id:
        return Response({'message': "No user_id in metadata"}, status=status.HTTP_200_OK)

    stripe_subscription_id = session.get('subscription')
    print("DEBUGGING SUB ID....", stripe_subscription_id)

    if stripe_subscription_id:
        sub, _created = Subscription.objects.get_or_create(user_id=user_id)

        if sub.stripe_subscription_id and sub.stripe_subscription_id != stripe_subscription_id:
            try:
                stripe.Subscription.cancel(sub.stripe_subscription_id)
            except Exception as e:
                print("Error canceling old subscription:", e)

        try:
            stripe.Subscription.modify(
                stripe_subscription_id,
                metadata=metadata,
            )
            print("subscription_modified....")
        except Exception as e:
            print("Error modifying subscription metadata:", e)

        period = metadata.get('period', 'monthly')
        sub.set_subscribe(period)
        sub.stripe_subscription_id = stripe_subscription_id
        sub.save()
    else:
        return handle_movie_series_purchase(metadata)

    print("save return response")
    return Response({'success': True}, status=status.HTTP_200_OK)


def handle_subscription_period_complete(metadata):
    print("handling subscription period complete:", metadata)
    user_id = metadata.get('user_id')
    if not user_id:
        return Response({'message': 'No user_id found in metadata'}, status=status.HTTP_200_OK)

    period = metadata.get('period', 'monthly')
    app_name = metadata.get('app_name')

    if app_name != "mom_pr":
        return Response({'message': 'Ignored: not mom_pr'}, status=status.HTTP_200_OK)

    sub = Subscription.objects.filter(user_id=user_id).first()
    if not sub:
        sub = Subscription.objects.create(user_id=user_id)

    sub.set_subscribe(period)
    sub.save()

    print("Subscription updated successfully")
    return Response({'success': True}, status=status.HTTP_200_OK)


def handle_invoice_payment_succeeded(event):
    invoice = event.get('data', {}).get('object', {})
    stripe_subscription_id = invoice.get('subscription')

    # Try extracting metadata from various possible Stripe invoice locations
    metadata = invoice.get('metadata') or {}
    if not metadata and 'subscription_details' in invoice and invoice['subscription_details']:
        metadata = invoice['subscription_details'].get('metadata') or {}
    if not metadata and 'parent' in invoice and isinstance(invoice['parent'], dict):
        metadata = invoice['parent'].get('subscription_details', {}).get('metadata') or {}

    # Check lines if metadata is still empty
    if not metadata:
        lines = invoice.get('lines', {}).get('data', [])
        if lines and isinstance(lines, list) and len(lines) > 0:
            metadata = lines[0].get('metadata') or {}

    if metadata and metadata.get('app_name') == 'mom_pr' and metadata.get('user_id'):
        return handle_subscription_period_complete(metadata)

    # Fallback: if metadata is not attached to invoice, look up existing subscription by stripe_subscription_id
    if stripe_subscription_id:
        sub = Subscription.objects.filter(stripe_subscription_id=stripe_subscription_id).first()
        if sub:
            period = sub.period or 'monthly'
            sub.set_subscribe(period)
            sub.save()
            print(f"Subscription renewed via stripe_subscription_id fallback for user {sub.user_id}")
            return Response({'success': True, 'message': 'Subscription renewed via fallback'}, status=status.HTTP_200_OK)

    print("invoice.payment_succeeded: No matching subscription found to renew")
    return Response({'status': 'ignored', 'message': 'Not a mom_pr subscription invoice'}, status=status.HTTP_200_OK)




