import datetime

from django.conf import settings
from django.db.models.expressions import (
    F, Exists, OuterRef, Q,
    Case, When, Value
)
from django.db import models
from django.db.models import Prefetch

from .serializers import MovieSerializer, SeriesSerializer
from .request_serializers import (
    SearchSerializer,
    WatchLaterRequestSerializer,
)


from .models import Movie, Series, Genre, Season, Episode


def search_movie(request, payload):
    search_query = SearchSerializer(data=payload)
    print("searching....")
    search_query.is_valid(raise_exception=True)

    print("validated.........")
    year_from = payload.get('year_from')
    year_to = payload.get('year_to')
    genres = payload.get('genres')
    title = payload.get('title')
    page_offset = payload.get('page_offset')

    print(year_from)
    print(title)
    print(year_to)
    n = payload.get('n')
    movie_list = Movie.objects.filter(publish=True)
    

    if request.user.is_authenticated:
        movie_list.annotate(user_lang=Value(
            request.user.language,
            output_field=models.CharField()
        ))
    movie_list = movie_list.annotate(
        is_collection=Exists(
            request.user.premium_collection.movies.filter(
                id=OuterRef('id'),
            )
        ),
        liked=Exists(
            request.user.likes.movies.filter(id=OuterRef('id'))
        ),
        disliked=Exists(
            request.user.dislikes.movies.filter(id=OuterRef('id'))
        ),
    )
    premium_ids = request.user.premium_collection.movies.values_list('id', flat=True)

    if year_from:
        movie_list = movie_list.filter(
            release_year__ge=year_from
        )

    if year_to:
        movie_list = movie_list.filter(
            release_year__le=year_to
        )

    if title:
        movie_list = movie_list.filter(
            title__icontains=title
        )

    if genres and isinstance(genres, list):

        for genre in genres:
            movie_list = movie_list.filter(
                genre=genre
            )
    if page_offset and isinstance(page_offset, int)\
            and page_count and isinstance(page_count, int):
        movie_list[page_offset: page_count]

    return movie_list


def search_series(request, payload):
    search_query = SearchSerializer(data=payload)
    search_query.is_valid(raise_exception=True)

    year_from = payload.get('year_from')
    year_to = payload.get('year_to')
    genres = payload.get('genres')
    title = payload.get('title')
    page_offset = payload.get('page_offset')
    n = payload.get('n')


    seasons = Season.objects.filter(publish=True)

    episodes = Episode.objects.filter(season__publish=True).annotate(
        is_collection=Exists(
            request.user.premium_collection.series.filter(
                id=OuterRef('id'),
            )
        ),
        liked=Exists(
            request.user.likes.series.filter(id=OuterRef('id'))
        ),
        disliked=Exists(
            request.user.likes.series.filter(id=OuterRef('id'))
        )
    )
    if request.user.is_authenticated:
        episodes.annotate(user_lang=Value(
            request.user.language,
            output_field=models.CharField()
        ))

    series_list = Series.objects.prefetch_related(
        Prefetch(
            'seasons',
            queryset=seasons
        ),

        Prefetch(
            'seasons__episodes',
            queryset=episodes
        ),
    )
    if request.user.is_authenticated:
        series_list.annotate(user_lang=Value(
            request.user.language,
            output_field=models.CharField()
        ))

    series_list = series_list.annotate(
        is_collection=Exists(
            request.user.premium_collection.series.filter(
                id=OuterRef('id')
            )
        ),
        liked=Exists(
            request.user.likes.series.filter(id=OuterRef('id'))
        ),
        disliked=Exists(
            request.user.dislikes.series.filter(id=OuterRef('id'))
        )

    )
    if year_from:
        series_list = series_list.filter(
            seasons__release_year__ge=year_from
        )

    if year_to:
        series_list = series_list.filter(
            seasons__release_year__le=year_to
        )

    if title:
        series_list = series_list.filter(
            name__icontains=title
        )

    if genres and isinstance(genres, list):

        for genre in genres:
            series_list = series_list.filter(
                genre=genre
            )

    if page_offset and isinstance(page_offset, int)\
            and page_count and isinstance(page_count, int):
        series_list[page_offset: page_count]

    return series_list


def get_all_movies(request):
    data = request.data if request.method == 'POST' else request.query_params
    search_query = SearchSerializer(data=data)
    search_query.is_valid(raise_exception=True)
    current_year = datetime.datetime.now().year
    previous_year = current_year - 1
    response = {}
    all_movies = search_movie(request, {})

    if request.user.is_authenticated:
        all_movies.annotate(user_lang=Value(
            request.user.language,
            output_field=models.CharField()
        ))

    response['popular'] = MovieSerializer(
        all_movies.filter(is_popular=True),
        many=True,
    ).data

    response['watch_later'] = MovieSerializer(
        request.user.watch_later.movies.annotate(

            is_collection=Exists(
                request.user.premium_collection.movies.filter(
                    id=OuterRef('id'),
                )
            ),
            liked=Exists(
                request.user.likes.movies.filter(id=OuterRef('id'))
            ),
            disliked=Exists(
                request.user.dislikes.movies.filter(id=OuterRef('id'))
            )
        ).all(),
        many=True
    ).data

    response['watch_history'] = MovieSerializer(
        request.user.watch_history.movies.annotate(
            is_collection=Exists(
                request.user.premium_collection.movies.filter(
                    id=OuterRef('id')
                )
            ),
            liked=Exists(
                request.user.likes.movies.filter(id=OuterRef('id'))
            ),
            disliked=Exists(
                request.user.dislikes.movies.filter(id=OuterRef('id'))
            ),
            user_lang=Value(
                request.user.language if request.user.is_authenticated else "en_US",
                output_field=models.CharField()
            )
        ).all(),
        many=True
    ).data

    response['previous_year'] = MovieSerializer(
        all_movies.filter(
            release_year=previous_year
        ).prefetch_related('genres').all(),
        many=True
    ).data
    for genre in Genre.objects.prefetch_related('movies').all():
        response[genre.slug] = MovieSerializer(
            genre.movies.annotate(
                is_collection=Exists(
                    request.user.premium_collection.series.filter(
                        id=OuterRef('id')
                    )
                ),
                liked=Exists(
                    request.user.likes.movies.filter(id=OuterRef('id'))
                ),
                disliked=Exists(
                    request.user.dislikes.movies.filter(id=OuterRef('id'))
                )
            ).all(),
            many=True
        ).data

    return response


def get_all_series(request):
    data = request.data if request.method == 'POST' else request.query_params
    search_query = SearchSerializer(data=data)
    search_query.is_valid(raise_exception=True)
    current_year = datetime.datetime.now().year
    previous_year = current_year - 1
    response = {}
    all_series = search_series(request, {})

    episodes = Episode.objects.filter(season__publish=True).annotate(
        is_collection=Exists(
            request.user.premium_collection.series.filter(
                id=OuterRef('id'),
            )
        ),
        liked=Exists(
            request.user.likes.series.filter(id=OuterRef('id'))
        ),
        disliked=Exists(
            request.user.dislikes.series.filter(id=OuterRef('id'))
        )
    )

    response['popular'] = SeriesSerializer(
        all_series.filter(
            is_popular=True
        ).prefetch_related(
            'genres',
        ).annotate(
            is_collection=Exists(
                request.user.premium_collection.series.filter(
                    id=OuterRef('id'),
                )
            ),
            liked=Exists(
                request.user.likes.series.filter(id=OuterRef('id'))
            ),
            disliked=Exists(
                request.user.dislikes.series.filter(id=OuterRef('id'))
            )
        ).all(),
        many=True,
    ).data
    response['watch_later'] = SeriesSerializer(
        request.user.watch_later.series.annotate(
            is_collection=Exists(
                request.user.premium_collection.series.filter(
                    id=OuterRef('id'),
                )
            ),
            liked=Exists(
                request.user.likes.series.filter(id=OuterRef('id'))
            ),
            disliked=Exists(
                request.user.dislikes.series.filter(id=OuterRef('id'))
            )

        ).all(),
        many=True
    ).data

    response['watch_history'] = SeriesSerializer(
        request.user.watch_history.series.prefetch_related(
            'genres',
        ).annotate(

            is_collection=Exists(
                request.user.premium_collection.series.filter(
                    id=OuterRef('id'),
                )
            ),
            liked=Exists(
                request.user.likes.series.filter(id=OuterRef('id'))
            ),
            disliked=Exists(
                request.user.dislikes.series.filter(id=OuterRef('id'))
            )

        ).all(),
        many=True
    ).data

    response['previous_year'] = SeriesSerializer(
        Series.objects.filter(
            seasons__release_year=previous_year
        ).prefetch_related('genres').all(),
        many=True
    ).data

    for genre in Genre.objects.prefetch_related('series_set').all():
        response[genre.slug] = SeriesSerializer(
            genre.series_set.annotate(
                is_collection=Exists(
                    request.user.premium_collection.series.filter(
                        id=OuterRef('id')
                    )
                ),
                liked=Exists(
                    request.user.likes.series.filter(id=OuterRef('id'))
                ),
                disliked=Exists(
                    request.user.dislikes.series.filter(id=OuterRef('id'))
                )
            ).all(),
            many=True
        ).data

    return response