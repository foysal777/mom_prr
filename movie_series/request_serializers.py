from rest_framework import serializers
from movie_series.models import Genre, Movie, Series


class SearchSerializer(serializers.Serializer):
    title = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    # title = serializers.CharField(
    #     # max_length=100,
    #     # default="",
    #     required=False,
    # )
    genres = serializers.MultipleChoiceField(
        choices=[genre.slug for genre in Genre.objects.all()],
        required=False
    )
    year_from = serializers.IntegerField(required=False)
    year_to = serializers.IntegerField(required=False)
    page_offset = serializers.IntegerField(
        required=False,
        min_value=0
    )
    n = serializers.IntegerField(
        required=False,
        min_value=1
    )


class WatchLaterRequestSerializer(serializers.Serializer):
    movie_set = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(),
        many=True,
        required=False,
    )

    series_set = serializers.PrimaryKeyRelatedField(
        queryset=Series.objects.all(),
        many=True,
        required=False,
    )

    movie_ids = serializers.SerializerMethodField(read_only=True)
    series_ids = serializers.SerializerMethodField(read_only=True)

    def get_movie_ids(self):
        return [movie.id for movie in movie_set]\
            if (movie_set := self.validated_data.get('movie_set')) else []

    def get_series_ids(self):
        return [series.id for series in series_set]\
            if (series_set := self.validated_data.get('series_set')) else []


class WatchHistoryRequestSerializer(serializers.Serializer):
    movie_set = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(),
        many=True,
        required=False,
    )

    series_set = serializers.PrimaryKeyRelatedField(
        queryset=Series.objects.all(),
        many=True,
        required=False,
    )

    movie_ids = serializers.SerializerMethodField(read_only=True)
    series_ids = serializers.SerializerMethodField(read_only=True)

    def get_movie_ids(self):
        return [movie.id for movie in movie_set]\
            if (movie_set := self.validated_data.get('movie_set')) else []

    def get_series_ids(self):
        return [series.id for series in series_set]\
            if (series_set := self.validated_data.get('series_set')) else []


