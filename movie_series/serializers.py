# catalog/serializers.py
from rest_framework import serializers
from .models import (
    Genre, Movie, Series, Season,
    Episode, WatchLater, VideoProgressStatus
)


class GenreMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name", "slug",)
        read_only_fields = fields


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreMiniSerializer(many=True, read_only=True)
    is_collection = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    alias_type = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()

    title = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()

    is_notify = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    class Meta:
        model = Movie
        fields = (
            "id", "title", "release_year", "runtime_minutes",
            "genres", "is_collection", "posters_url",
            "is_premium", "premium_price_usd",
            "premium_price_gourde", "description",
            "alias_type", 'file_uuid', "comming_soon_time",
            "likes", "dislikes", "liked", "disliked", "trailer",
            "is_notify"
        )
        read_only_fields = fields  # entire serializer is read-only

    def get_title(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.title_fr if instance.user_lang == 'fr_FR'
                else instance.title if instance.user_lang == 'en_US' else instance.title_es
            )
        return instance.title

    def get_description(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.description_fr if instance.user_lang == 'fr_FR'
                else instance.description if instance.user_lang == 'en_US' else instance.description_es
            )
        return instance.title


    def get_is_collection(self, instance):
        if hasattr(instance, 'is_collection'):
            return instance.is_collection
        else:
            return None

    def get_is_premium(self, instance):
        return instance.is_premium

    def get_alias_type(self, instance):
        return 'movie'

    def get_likes(self, instance): return instance.likes

    def get_dislikes(self, instance): return instance.dislikes

    def get_liked(self, instance):
        if hasattr(instance, 'liked'):
            return instance.liked
        return False

    def get_disliked(self, instance):
        if hasattr(instance, 'disliked'):
            return instance.disliked
        return False

    def get_is_notify(self, instance):
        if hasattr(instance, 'is_notify') and instance.is_notify:
            return True
        return False


class MovieDetailSerializer(serializers.ModelSerializer):
    genres = GenreMiniSerializer(many=True, read_only=True)
    is_collection = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    alias_type = serializers.SerializerMethodField()
    related_movies = serializers.SerializerMethodField()

    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            "id", "title", "release_year", "runtime_minutes",
            "genres", "is_collection", "posters_url",
            "is_premium", "premium_price_usd",
            "premium_price_gourde", "description",
            "alias_type", 'file_uuid', 'related_movies',
            "comming_soon_time", "likes", "dislikes",
            "liked", "disliked", "trailer"
        )
        read_only_fields = fields  # entire serializer is read-only

    def get_title(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.title_fr if instance.user_lang == 'fr_FR'
                else instance.title if instance.user_lang == 'en_US' else instance.title_es
            )
        return instance.title

    def get_description(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.description_fr if instance.user_lang == 'fr_FR'
                else instance.description if instance.user_lang == 'en_US' else instance.description_es
            )
        return instance.title


    def get_likes(self, instance): return instance.likes

    def get_dislikes(self, instance): return instance.dislikes

    def get_liked(self, instance):
        if hasattr(instance, 'liked'):
            return instance.liked
        return False

    def get_disliked(self, instance):
        if hasattr(instance, 'disliked'):
            return instance.disliked
        return False

    def get_related_movies(self, instance):
        genre_ids = instance.genres.values_list(
            'id', flat=True
        )
        related_movies = Movie.objects.filter(
            genres__in=genre_ids
        ).exclude(id=instance.id)
        return MovieSerializer(related_movies, many=True).data

    def get_is_collection(self, instance):
        if hasattr(instance, 'is_collection'):
            return instance.is_collection
        else:
            return None

    def get_is_premium(self, instance):
        return instance.is_premium

    def get_alias_type(self, instance):
        return 'movie'


class EpisodeSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = (
            "id", "season_id", "title", "created_at",
            "updated_at", "file_uuid", "trailer",
            "likes", "dislikes", "liked", "disliked"
        )
        read_only_fields = fields

    def get_title(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.title_fr if instance.user_lang == 'fr_FR'
                else instance.title if instance.user_lang == 'en_US' else instance.title_es
            )
        return instance.title

    def get_likes(self, instance): return instance.likes

    def get_dislikes(self, instance): return instance.dislikes

    def get_liked(self, instance):
        if hasattr(instance, 'liked'):
            return instance.liked
        return False

    def get_disliked(self, instance):
        if hasattr(instance, 'disliked'):
            return instance.disliked
        return False


class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    series_name = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    posters_url = serializers.SerializerMethodField()

    is_notify = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = (
            "id", "series_id", "season_name",
            "release_year", "created_at",
            "updated_at", "episodes", 'series_name',
            "comming_soon_time", "genres", "posters_url",
            "is_notify"
        )
        read_only_fields = fields

    def get_genres(self, instance):
        return GenreMiniSerializer(
            instance.series.genres, many=True
        ).data

    def get_series_name(self, instance):
        if hasattr(instance, "series_name"):
            return instance.series_name
        return ""

    def get_posters_url(self, instance):
        return instance.series.posters_url

    def get_is_notify(self, instance):
        if hasattr(instance, 'is_notify') and instance.is_notify:
            return True
        return False


class SeriesSerializer(serializers.ModelSerializer):
    genres = GenreMiniSerializer(many=True, read_only=True)
    is_collection = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    alias_type = serializers.SerializerMethodField()

    name = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = (
            "id", "name", "genres", "created_at", "is_premium",
            "updated_at", "is_collection", "posters_url",
            "premium_price_usd", "premium_price_gourde",
            "description", "alias_type",
            "likes", "dislikes", "liked", "disliked"

        )
        read_only_fields = fields

    def get_name(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.name_fr if instance.user_lang == 'fr_FR'
                else instance.name if instance.user_lang == 'en_US' else instance.name_es
            )
        return instance.name


    def get_likes(self, instance): return instance.likes

    def get_dislikes(self, instance): return instance.dislikes

    def get_liked(self, instance):
        if hasattr(instance, 'liked'):
            return instance.liked
        return False

    def get_disliked(self, instance):
        if hasattr(instance, 'disliked'):
            return instance.disliked
        return False

    def get_is_collection(self, instance):
        if hasattr(instance, 'is_collection'):
            return instance.is_collection
        else:
            return False

    def get_is_premium(self, instance):
        return instance.is_premium

    def get_alias_type(self, instance):
        return 'series'

    def get_description(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.description_fr if instance.user_lang == 'fr_FR'
                else instance.description if instance.user_lang == 'en_US' else instance.description_es
            )
        return instance.description



class SeasonWithEpisodesSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    series_name = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = (
            "id", "series_id", "episodes",
            "created_at", "updated_at",
            "comming_soon_time"
        )
        read_only_fields = fields

    # def get_series_name(self, instance):
    #     return instance.series.name

    def get_series_name(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.series.name_fr if instance.user_lang == 'fr_FR'
                else instance.series.name if instance.user_lang == 'en_US' else instance.series.name_es
            )
        return instance.series.name


class SeriesDetailSerializer(serializers.ModelSerializer):
    genres = GenreMiniSerializer(many=True, read_only=True)
    seasons = SeasonWithEpisodesSerializer(many=True, read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = ("id", "name", "release_year", "genres", "seasons", "created_at", "updated_at")
        read_only_fields = fields

    def get_name(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.name_fr if instance.user_lang == 'fr_FR'
                else instance.name if instance.user_lang == 'en_US' else instance.name_es
            )
        return instance.name

# NEW IMPLEMENTATION
# NEW IMPLEMENTATION
# NEW IMPLEMENTATION
# NEW IMPLEMENTATION
# NEW IMPLEMENTATION
class SearchAllSerializer(serializers.Serializer):
    title = serializers.CharField(
        max_length=100,
        required=False,
    )


class SeriesFullSerializer(serializers.ModelSerializer):
    seasons = SeasonSerializer(many=True, read_only=True)
    genres = GenreMiniSerializer(many=True, read_only=True)
    is_collection = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    alias_type = serializers.SerializerMethodField()
    related_series = serializers.SerializerMethodField()

    name = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = (
            "id", "name", "genres", "created_at",
            "is_premium", "updated_at", "is_collection",
            "posters_url", "premium_price_usd",
            "premium_price_gourde", "description",
            'seasons', 'alias_type', "related_series",
            'likes', 'dislikes', 'liked', 'disliked'
        )
        read_only_fields = fields

    def get_name(self, instance):
        if hasattr(instance, 'user_lang'):
            return (
                instance.name_fr if instance.user_lang == 'fr_FR'
                else instance.name if instance.user_lang == 'en_US' else instance.name_es
            )
        return instance.name
    def get_likes(self, instance): return instance.likes

    def get_dislikes(self, instance): return instance.dislikes

    def get_liked(self, instance):
        if hasattr(instance, 'liked'):
            return instance.liked
        return False

    def get_disliked(self, instance):
        if hasattr(instance, 'disliked'):
            return instance.disliked
        return False

    def get_related_series(self, instance):
        genre_ids = instance.genres.values_list(
            'id', flat=True
        )
        related_series = Series.objects.filter(
            genres__in=genre_ids
        ).exclude(id=instance.id)

        dummy_related_series = Series.objects.all()[:2]
        return SeriesSerializer(dummy_related_series, many=True).data
        pass

    def get_alias_type(self, instance):
        return "series"

    def get_is_collection(self, instance):
        if hasattr(instance, 'is_collection'):
            return instance.is_collection
        else:
            return None

    def get_is_premium(self, instance):
        return instance.is_premium

    def get_alias_type(self, instance):
        return 'series'


class WatchLaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchLater
        fields = "__all__"


class VideoProgressStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgressStatus
        fields = "__all__"