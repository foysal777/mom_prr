from django.db.models import Q
from django.conf import settings

from rest_framework import serializers
from movie_series.models import Movie, Series


class SubscriptionRequestSerializer(serializers.Serializer):
    # success_url = serializers.URLField(
    #     default="https://example.com",
    #     required=False
    # )
    # cancel_url = serializers.URLField(
    #     required=False,
    #     default="https://example.com?error=error"
    # )
    period = serializers.ChoiceField(choices=(
        ('monthly', 'monthly'),
        ('yearly', 'yearly')
    ))
    is_moncash = serializers.BooleanField(default=False)


class MovieSeriesPurchaseRequestSerializer(serializers.Serializer):
    movie_set = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.filter(
            Q(premium_price_usd__gt=0.0)
            | Q(premium_price_gourde__gt=0.0)
        ),
        many=True,
        required=False,
        error_messages={
            'does_not_exist': 'some of the selected are not premium',
            'incorrect_type': 'Incorrect type. Expected pk value, received {data_type}.'
        }
    )

    series_set = serializers.PrimaryKeyRelatedField(
        queryset=Series.objects.filter(
            Q(premium_price_usd__gt=0.0)
            | Q(premium_price_gourde__gt=0.0)
        ),        many=True,
        required=False,
        error_messages={
            'does_not_exist': 'some of the selected are not premium',
            'incorrect_type': 'Incorrect type. Expected pk value, received {data_type}.'
        }
    )
    is_moncash = serializers.BooleanField(default=False)

    movie_ids = serializers.SerializerMethodField(read_only=True)
    series_ids = serializers.SerializerMethodField(read_only=True)

    def get_movie_ids(self):
        return [movie.id for movie in movie_set]\
            if (movie_set := self.validated_data.get('movie_set')) else []

    def get_series_ids(self):
        return [series.id for series in series_set]\
            if (series_set := self.validated_data.get('series_set')) else []


class RevenueCatSyncSerializer(serializers.Serializer):
    PURCHASE_TYPES = (
        ('subscription', 'Subscription'),
        ('movie', 'Movie'),
        ('series', 'Series'),
    )
    purchase_type = serializers.ChoiceField(choices=PURCHASE_TYPES)
    
    # For subscriptions
    period = serializers.ChoiceField(choices=(
        ('monthly', 'monthly'),
        ('yearly', 'yearly')
    ), required=False)
    
    # For one-time purchases
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(), required=False
    )
    series_id = serializers.PrimaryKeyRelatedField(
        queryset=Series.objects.all(), required=False
    )

    def validate(self, data):
        p_type = data.get('purchase_type')
        if p_type == 'subscription' and not data.get('period'):
            raise serializers.ValidationError({"period": "Required for subscription"})
        if p_type == 'movie' and not data.get('movie_id'):
            raise serializers.ValidationError({"movie_id": "Required for movie purchase"})
        if p_type == 'series' and not data.get('series_id'):
            raise serializers.ValidationError({"series_id": "Required for series purchase"})
        return data
