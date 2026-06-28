# catalog/urls.py
from django.urls import path

from rest_framework.routers import DefaultRouter
from .views import (
    search_all,
    movies_all,
    # SeriesListView,
    video_event_webhook,
    get_video_playlist,
    SeriesDetailView,
    MovieDetailView,
    get_watch_later,
    series_all,
    premium_collection,
    get_pupular_movie_series,
    add_to_watch_later,
    remove_from_watch_later,
    get_genre_list,
    movies_by_genre, series_by_genre,
    get_all_movie_series,
    get_watch_history,
    get_comming_soon,
    remove_from_watch_history,
    like_movie, dislike_movie,
    like_episode, dislike_episode,
    like_series, dislike_series,
    notify_movie, notify_seasons,
    save_progress, get_progress, get_all_progress,
    public_movie_list
)

# router = DefaultRouter()
# router.register(r"movies", MovieViewSet, basename="movie")
# router.register(r"series", SeriesViewSet, basename="series")

# urlpatterns = router.urls
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


class MySeri(serializers.Serializer):
    title = serializers.CharField(
        required=False,
    )


@api_view(['get'])
def my_funk(request):
    ser = MySeri(data=request.data)
    ser.is_valid(raise_exception=True)
    return Response({
        "msg": "success"
        })
    pass


urlpatterns = [
    path("movies/public/", public_movie_list, name="movies-public"),
    path("genres/", get_genre_list, name="genre-list"),
    path("search_all/", search_all, name="search-all"),
    path("all/", get_all_movie_series, name="search-all"),
    path("comming_soon/", get_comming_soon, name="search-all"),
    path("watch_later/", get_watch_later),
    path("watch_later_add/", add_to_watch_later),
    path("watch_later_remove/", remove_from_watch_later),
    path("watch_later_remove/", remove_from_watch_later),
    path("watch_history/", get_watch_history),
    path("remove_from_watch_history/", remove_from_watch_history),
    # path("popular/", get_pupular_movie_series),
    path("movies/all/", movies_all, name="movie-list"),
    path(
        "movies/by_genre/<str:genre_slug>/",
        movies_by_genre, name="movie-by-genre"
    ),
    path(
        "series/by_genre/<str:genre_slug>/",
        series_by_genre, name="series-by-genre"
    ),
    path("series/all/", series_all, name="series-list"),

    path(
        "series/<int:pk>/detail/",
        SeriesDetailView.as_view(),
        name="series-detail"
    ),
    path(
        "movie/<int:pk>/detail/",
        MovieDetailView.as_view(),
        name="movie-detail"
    ),

    path("<str:file_uuid>/get_video_playlist/", get_video_playlist),
    path("video_events/", video_event_webhook),
    path("premium_collection/", premium_collection),
    path("movie/<int:pk>/like", like_movie),
    path("movie/<int:pk>/dislike", dislike_movie),
    path("episode/<int:pk>/like", like_episode),
    path("episode/<int:pk>/dislike", dislike_episode),

    path("series/<int:pk>/like", like_series),
    path("series/<int:pk>/dislike", dislike_series),


    path("movies/<int:pk>/notify/", notify_movie),
    path("seasons/<int:pk>/notify/", notify_seasons),

    path("save_progress/", save_progress),
    path("<str:file_uuid>/get_progress/", get_progress),
    path("continue_progress/", get_all_progress),
    # path("test_endpoint/", my_funk),
]