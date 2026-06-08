# catalog/views_list.py

import json
import datetime

from django.db.models import Prefetch
from django.conf import settings
from django.db.models.expressions import (
    F, Exists, OuterRef, Q,
    Case, When, Value
)
from django.db.models import Prefetch
from django.db import models

from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.generics import (
    RetrieveAPIView, CreateAPIView
)

from . import utils

from .models import (
    Movie, Series, Genre,
    WatchLater, SearchHistory,
    Episode, WatchHistory, Season,
    VideoProgressStatus
)

from .serializers import (
    SearchAllSerializer,
    MovieSerializer, SeriesSerializer,
    SeasonSerializer, SeriesFullSerializer,
    WatchLaterSerializer, MovieDetailSerializer,
    VideoProgressStatusSerializer, EpisodeSerializer
)

from .request_serializers import (
    SearchSerializer, WatchLaterRequestSerializer,
    WatchHistoryRequestSerializer
)


from .filters import MovieFilter, SeriesFilter, SeasonFilter

from .vdocipher_event_handelers import VDOCIPHER_EVENT_HANDLERS
from .vdocipher_client import VdocipherClient

vdo_cli = VdocipherClient()

REDIS_CLIENT = settings.REDIS_CLIENT


@api_view(['GET'])
def get_genre_list(request):
    return Response({
        'genres': [genre.slug for genre in Genre.objects.all()]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pupular_movie_series(request):
    movie_list = Movie.objects.filter(
        is_popular=True,
        publish=True
    ).annotate(user_lang=Value(
        request.user.language,
        output_field=models.CharField()
    ))

    series_list = Series.objects.filter(
        is_popular=True,
        publish=True
    ).annotate(user_lang=Value(
        request.user.language,
        output_field=models.CharField()
    ))

    return Response({
        "data": {
            "movies": MovieSerializer(movie_list, many=True).data,
            "series": SeriesSerializer(series_list, many=True).data
        }
    })


class SeriesDetailView(RetrieveAPIView):
    serializer_class = SeriesFullSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        request = self.request
        return Series.objects.annotate(
            is_collection=Exists(
                request.user.premium_collection.movies.filter(
                    id=OuterRef('id')
                )
            ),
            liked=Exists(
                request.user.likes.series.filter(id=OuterRef('id'))
            ),
            disliked=Exists(
                request.user.dislikes.series.filter(id=OuterRef('id'))
            ),
            user_lang=Value(
                request.user.language,
                output_field=models.CharField()
        )).all()

    # def get_object(self):
    #     pk = self.kwargs.get('pk')
    #     return super().get_queryset().prefetch_related(
    #         "seasons",
    #         "seasons__episodes"
    #     ).get(id=pk)


class MovieDetailView(RetrieveAPIView):
    # serializer_class = MovieSerializer
    serializer_class = MovieDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        request = self.request
        return Movie.objects.annotate(
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
                request.user.language,
                output_field=models.CharField()
        )).all()

    # def get_object(self):
    #     pk = self.kwargs.get('pk')
    #     return super().get_queryset().get(id=pk)


@extend_schema(request=SearchAllSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_all(request):
    title = request.data.get('title')
    if title or True:
        payload = {
            "title": title
        }
        if title:
            SearchHistory.objects.create(
                query=title,
                user=request.user
            )

        return Response({
            "data": {
                "movies": MovieSerializer(
                    utils.search_movie(request, payload),
                    many=True
                ).data,
                "series": SeriesSerializer(
                    utils.search_series(request, payload),
                    many=True
                ).data
            }
        })

    # print("DEBUG SEARCH ALL")
    # print("DEBUG SEARCH ALL")
    # print("DEBUG SEARCH ALL")
    search_history = request.user.search_history.all()
    q_series = Q()
    q_movies = Q()
    for record in search_history:
        q_movies |= Q(title__icontains=record.query)
        q_series |= Q(name__icontains=record.query)

    movies = MovieSerializer(Movie.objects.filter(
        q_movies
    )).data

    series = MovieSerializer(Movie.objects.filter(
        q_series
    )).data

    return Response({
        "data": {
            "movies": movies,
            "series": series
        }
    })


@extend_schema(responses=MovieSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def movies_all(request):
    return Response({
        "data": utils.get_all_movies(request)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def movies_by_genre(request, genre_slug):
    genre = Genre.objects.filter(slug=genre_slug).first()
    if not genre:
        raise ValidationError({
            "error": "no genre available with that slug-name"
        })
    current_year = datetime.datetime.now().year
    previous_year = current_year - 1
    response = {}
    all_movies = genre.movies.annotate(
        is_collection=Exists(
            request.user.premium_collection.series.filter(
                id=OuterRef('id')
            )
        )
    )
    response['popular'] = MovieSerializer(
        all_movies.filter(is_popular=True),
        many=True,
    ).data

    response['watch_later'] = MovieSerializer(
        all_movies.filter(
            watchlater__user=request.user
        ).prefetch_related("genres"),
        many=True
    ).data

    response['previous_year'] = MovieSerializer(
        all_movies.filter(
            release_year=previous_year,
        ).prefetch_related('genres').all(),
        many=True
    ).data
    return Response({
        "data": response
    })


@extend_schema(responses=SeriesFullSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def series_all(request):
    return Response({
        "data": utils.get_all_series(request)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_all_movie_series(request):
    return Response({
        'data': {
            'movies': utils.get_all_movies(request),
            'series': utils.get_all_series(request)
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def series_by_genre(request, genre_slug):
    genre = Genre.objects.filter(slug=genre_slug).first()
    if not genre:
        raise ValidationError({
            "error": "no genre available with that slug-name"
        })
    current_year = datetime.datetime.now().year
    previous_year = current_year - 1
    response = {}
    all_series = genre.series_set.annotate(
        is_collection=Exists(
            request.user.premium_collection.series.filter(
                id=OuterRef('id')
            )
        )
    )
    response['popular'] = SeriesSerializer(
        all_series.filter(is_popular=True),
        many=True,
    ).data

    response['watch_later'] = SeriesSerializer(
        all_series.filter(
            watchlater__user=request.user
        ).prefetch_related("genres"),
        many=True
    ).data

    response['previous_year'] = MovieSerializer(
        all_series.filter(
            seasons__release_year=previous_year,
        ).prefetch_related('genres').all(),
        many=True
    ).data
    return Response({
        "data": response
    })


@api_view(['get'])
@permission_classes([IsAuthenticated])
def get_watch_later(request):

    obj, _created = WatchLater.objects.get_or_create(
        user=request.user,
    )
    return Response({
        "data": {
            "movies": MovieSerializer(
                obj.movies, many=True
            ).data,
            "series": SeriesSerializer(
                obj.series, many=True
            ).data
        }
    })


@extend_schema(request=WatchLaterRequestSerializer)
@api_view(['patch'])
@permission_classes([IsAuthenticated])
def add_to_watch_later(request):
    req_ser = WatchLaterRequestSerializer(data=request.data)
    req_ser.is_valid(raise_exception=True)
    movie_set = req_ser.validated_data.get('movie_set', [])
    series_set = req_ser.validated_data.get('series_set', [])

    # print(series_set)
    request.user.watch_later.movies.add(*movie_set)
    request.user.watch_later.series.add(*series_set)
    return Response({
        "success": True
    })


@extend_schema(request=WatchLaterRequestSerializer)
@api_view(['patch'])
@permission_classes([IsAuthenticated])
def remove_from_watch_later(request):
    req_ser = WatchLaterRequestSerializer(data=request.data)
    req_ser.is_valid(raise_exception=True)
    movie_set = req_ser.validated_data.get('movie_set', [])
    series_set = req_ser.validated_data.get('series_set', [])

    # print(series_set)
    request.user.watch_later.movies.remove(*movie_set)
    request.user.watch_later.series.remove(*series_set)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_video_playlist(request, file_uuid):
    is_offline = request.query_params.get('offline', False)
    if False and not request.user.is_subscribed():
        raise ValidationError({"error": "you must be subscribed"})

    movie = Movie.objects.filter(file_uuid=file_uuid).first()
    series = Series.objects.filter(
        seasons__episodes__file_uuid=file_uuid
    ).first()

    if movie:
        request.user.watch_history.movies.add(movie)
    if series:
        request.user.watch_history.series.add(series)

    if False and movie and movie.is_premium and movie not in \
            request.user.premium_collection.movies:
        raise ValidationError({
            "error": "You must buy it."
        })
    elif False and series and series.is_premium and series not in \
            request.user.premium_collection.series:
        raise ValidationError({
            "error": "You must buy it."
        })
    elif False and movie and not (
        movie.is_premium or request.user.is_subscribed
    ):
        raise ValidationError({
            "error": "you must be subscribed"
        })

    if is_offline:
        play_list_info, _err = vdo_cli.get_offline_playlist(file_uuid)
    else:
        play_list_info, _err = vdo_cli.get_playlist_info(file_uuid)


    if _err:
        raise ValidationError({"error": _err})

    progress = VideoProgressStatus.objects.filter(file_uuid=file_uuid).first()


    if progress:
        play_list_info['progress'] = VideoProgressStatusSerializer(progress).data
    else:
        play_list_info['progress'] = None

    return Response(play_list_info)

{
    "otp": "",
    "paydf": "",
    "file_uuid": "",    
    "last_position_seconds": "",
    "total_duration_seconds": ""
}

@extend_schema(exclude=True)
@api_view(['POST'])
def video_event_webhook(request):
    event = request.data.get('event')
    webhook_secret = request.query_params.get('secret_key')
    if webhook_secret != settings.VDOCIPHER_WEBHOOK_SECRET:
        raise ValidationError({"error": "invalid sender"})

    # signal all recent handlers for the same video event to abort.
    # as this call will handle it now.
    REDIS_CLIENT.publish(f"{event}", "ABORT")

    timeout = 5

    pubsub = REDIS_CLIENT.pubsub()
    pubsub.subscribe(f"{event}")

    # safely clears the default subscription confirmation message
    pubsub.get_message(f"{event}")

    # wait if same event occurs in the same video in short time.
    # if same event occurs in the same video then abort
    # and the new call will handle.
    while (new_message := pubsub.get_message(f"{event}", timeout)):
        if new_message['type'] == "message"\
                and new_message['data'].decode() == 'ABORT':
            return Response({
                "abort": "duo to another update."
            })

    pubsub.unsubscribe(f"{event}")

    return VDOCIPHER_EVENT_HANDLERS[event](request.data['payload'])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def premium_collection(request):
    movie_ser = MovieSerializer(
        request.user.premium_collection.movies,
        many=True
    )

    series_ser = SeriesSerializer(
        request.user.premium_collection.series,
        many=True
    )
    return Response({
        "data": {
            "movies": movie_ser.data,
            "series": series_ser.data
        }
    })


@api_view(['get'])
@permission_classes([IsAuthenticated])
def get_watch_history(request):

    obj, _created = WatchHistory.objects.get_or_create(
        user=request.user,
    )
    return Response({
        "data": {
            "movies": MovieSerializer(
                obj.movies, many=True
            ).data,
            "series": SeriesSerializer(
                obj.series, many=True
            ).data
        }
    })

from django.db.models import Case, Value, BooleanField, When
from django.db.models.expressions import RawSQL

@api_view(['get'])
@permission_classes([IsAuthenticated])
def get_comming_soon(request):

    movies = Movie.objects.filter(
        publish=False
    ).order_by('-id')

    for movie in movies:
        if request.user.id in movie.notifyees:
            movie.is_notify=True



    seasons = Season.objects.select_related("series").filter(
        publish=False
    ).order_by('-id').annotate(
        series_name=Value("series__name")
    )
    for season in seasons:
        if request.user.id in movie.notifyees:
            movie.is_notify=True


    series = Series.objects.prefetch_related(
        Prefetch('seasons', queryset=seasons)
    ).filter(
        seasons__publish=False
    )
    return Response({
        "data": {
            "movies": MovieSerializer(
                movies, many=True
            ).data,
            "series": SeasonSerializer(
                seasons, many=True
            ).data
        }
    })


# @extend_schema(request=WatchLaterRequestSerializer)
# @api_view(['patch'])
# @permission_classes([IsAuthenticated])
# def add_to_watch_later(request):
#     req_ser = WatchLaterRequestSerializer(data=request.data)
#     req_ser.is_valid(raise_exception=True)
#     movie_set = req_ser.validated_data.get('movie_set', [])
#     series_set = req_ser.validated_data.get('series_set', [])

#     # print(series_set)
#     request.user.watch_later.movies.add(*movie_set)
#     request.user.watch_later.series.add(*series_set)
#     return Response({
#         "success": True
#     })


@extend_schema(request=WatchHistoryRequestSerializer)
@api_view(['patch'])
@permission_classes([IsAuthenticated])
def remove_from_watch_history(request):
    req_ser = WatchHistoryRequestSerializer(data=request.data)
    req_ser.is_valid(raise_exception=True)
    movie_set = req_ser.validated_data.get('movie_set', [])
    series_set = req_ser.validated_data.get('series_set', [])

    # print(series_set)
    request.user.watch_history.movies.remove(*movie_set)
    request.user.watch_history.series.remove(*series_set)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_movie(request, pk):
    movie = get_object_or_404(Movie, id=pk)
    movie.like_set.add(request.user.likes)
    movie.dislike_set.remove(request.user.dislikes)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dislike_movie(request, pk):
    movie = get_object_or_404(Movie, id=pk)
    movie.dislike_set.add(request.user.dislikes)
    movie.like_set.remove(request.user.likes)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_episode(request, pk):
    episode = get_object_or_404(Episode, id=pk)
    episode.like_set.add(request.user.likes)
    episode.dislike_set.remove(request.user.dislikes)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dislike_episode(request, pk):
    episode = get_object_or_404(Episode, id=pk)
    episode.dislike_set.add(request.user.dislikes)
    episode.like_set.remove(request.user.likes)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_series(request, pk):
    series = get_object_or_404(Series, id=pk)
    series.like_set.add(request.user.likes)
    series.dislike_set.remove(request.user.dislikes)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dislike_series(request, pk):
    series = get_object_or_404(Series, id=pk)
    series.dislike_set.add(request.user.dislikes)
    series.like_set.remove(request.user.likes)
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notify_movie(request, pk):
    movie = get_object_or_404(Movie, id=pk)
    if request.user.id not in movie.notifyees:
        movie.notifyees.append(request.user.id)

    movie.save()
    return Response({
        "success": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notify_seasons(request, pk):
    season = get_object_or_404(Season, id=pk)
    if request.user.id not in season.notifyees:
        season.notifyees.append(request.user.id)

    season.save()
    return Response({
        "success": True
    })


@extend_schema(request=VideoProgressStatusSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_progress(request):
    ser = VideoProgressStatusSerializer(data=request.data)
    # ser.is_valid(raise_exception=True)
    
    process = VideoProgressStatus.objects.update_or_create(
        file_uuid=request.data['file_uuid'],
        defaults={
            **request.data
        },
        create_defaults={
            **request.data
        }
    )

    # ser.save()
    return Response({
        "success": True
    })


@extend_schema(request=VideoProgressStatusSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_progress(request, file_uuid):
    progress = get_object_or_404(VideoProgressStatus, file_uuid=file_uuid)
    ser = VideoProgressStatusSerializer(progress)

    return Response({
        "progress": ser.data
    })

from django.forms.models import model_to_dict

from django.db.models import OuterRef, Subquery
from django.forms.models import model_to_dict

@extend_schema(request=VideoProgressStatusSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_progress(request):
    progress_map = {
        obj.file_uuid: obj
        for obj in VideoProgressStatus.objects.all()
    }

    last_updated_subquery = VideoProgressStatus.objects.filter(
        file_uuid=OuterRef('file_uuid')
    ).values('last_updated')[:1]

    movies = Movie.objects.filter(
        file_uuid__in=progress_map.keys()
    ).annotate(
        last_updated=Subquery(last_updated_subquery)
    ).order_by('-last_updated')

    episodes = Episode.objects.filter(
        file_uuid__in=progress_map.keys()
    ).annotate(
        last_updated=Subquery(last_updated_subquery)
    ).order_by('-last_updated')

    movie_data_set = MovieDetailSerializer(movies, many=True).data
    episode_data_set = EpisodeSerializer(episodes, many=True).data

    return Response({
        "movies": [
            {
                **movie_data,
                "status": model_to_dict(progress_map[movie_data['file_uuid']])
            }
            for movie_data in movie_data_set
        ],
        "episodes": [
            {
                **episode_data,
                "status": model_to_dict(progress_map[episode_data['file_uuid']])  # fix: was movie_data
            }
            for episode_data in episode_data_set
        ],
    })
