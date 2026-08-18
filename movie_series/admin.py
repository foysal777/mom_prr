from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    Genre, Movie, Series,
    Season, Episode, WatchHistory,
    WatchLater, PremiumCollection, Like,
    DisLike, SearchHistory, VideoProgressStatus
)


@admin.action(description="Mark selected items as published")
def make_published(modeladmin, request, queryset):
    queryset.update(publish=True)


@admin.action(description="Mark selected items as unpublished")
def make_unpublished(modeladmin, request, queryset):
    queryset.update(publish=False)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'movies_count', 'series_count', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']

    @admin.display(description='Movies')
    def movies_count(self, obj):
        return obj.movies.count()

    @admin.display(description='Series')
    def series_count(self, obj):
        return obj.series_set.count()


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'poster_preview',
        'release_year',
        'display_genres',
        'runtime_minutes',
        'premium_price_usd',
        'premium_price_gourde',
        'user_views_count',
        'view_count',
        'is_popular',
        'publish',
        'created_at'
    ]
    list_filter = [
        'publish',
        'is_popular',
        'release_year',
        'genres',
        'created_at'
    ]
    search_fields = [
        'title',
        'title_fr',
        'title_es',
        'description',
        'file_uuid'
    ]
    list_editable = [
        'publish',
        'is_popular'
    ]
    filter_horizontal = ['genres']
    actions = [make_published, make_unpublished]
    ordering = ['-created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            annotated_user_views=Count('watchhistory', distinct=True)
        )

    def get_form(self, request, obj, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'upload_video' in form.base_fields.keys():
            form.base_fields.pop('upload_video')
        return form

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [
            'file_uuid',
            'notifyees',
            'created_at',
            'updated_at'
        ]

    @admin.display(description='Genres')
    def display_genres(self, obj):
        return ", ".join([g.name for g in obj.genres.all()[:3]]) or "-"

    @admin.display(description='Poster')
    def poster_preview(self, obj):
        if obj.poster_url:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />', obj.poster_url.url)
        elif obj.posters_url and len(obj.posters_url) > 0:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />', obj.posters_url[0])
        return "-"

    @admin.display(description='User Views', ordering='annotated_user_views')
    def user_views_count(self, obj):
        if hasattr(obj, 'annotated_user_views'):
            return obj.annotated_user_views
        return obj.watchhistory_set.count()


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0
    fields = ['title', 'title_fr', 'title_es', 'file_uuid']
    readonly_fields = ['file_uuid']


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 0
    fields = ['season_name', 'release_year', 'comming_soon_time', 'publish']


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'poster_preview',
        'display_genres',
        'seasons_count',
        'premium_price_usd',
        'premium_price_gourde',
        'user_views_count',
        'view_count',
        'is_popular',
        'created_at'
    ]
    list_filter = [
        'is_popular',
        'genres',
        'created_at'
    ]
    search_fields = [
        'name',
        'name_fr',
        'name_es',
        'description'
    ]
    list_editable = [
        'is_popular'
    ]
    filter_horizontal = ['genres']
    inlines = [SeasonInline]
    ordering = ['-created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            annotated_user_views=Count('watchhistory', distinct=True)
        )

    @admin.display(description='Poster')
    def poster_preview(self, obj):
        if obj.poster_url:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />', obj.poster_url.url)
        elif obj.posters_url and len(obj.posters_url) > 0:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />', obj.posters_url[0])
        return "-"

    @admin.display(description='Genres')
    def display_genres(self, obj):
        return ", ".join([g.name for g in obj.genres.all()[:3]]) or "-"

    @admin.display(description='Seasons')
    def seasons_count(self, obj):
        return obj.seasons.count()

    @admin.display(description='User Views', ordering='annotated_user_views')
    def user_views_count(self, obj):
        if hasattr(obj, 'annotated_user_views'):
            return obj.annotated_user_views
        return obj.watchhistory_set.count()


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = [
        'series',
        'season_name',
        'episodes_count',
        'release_year',
        'comming_soon_time',
        'publish',
        'created_at'
    ]
    list_filter = [
        'publish',
        'release_year',
        'series',
        'created_at'
    ]
    search_fields = [
        'season_name',
        'series__name'
    ]
    list_editable = [
        'publish'
    ]
    actions = [make_published, make_unpublished]
    inlines = [EpisodeInline]
    ordering = ['series', 'season_name']

    def get_readonly_fields(self, request, obj=None):
        return [
            'notifyees',
            'created_at',
            'updated_at'
        ]

    @admin.display(description='Episodes')
    def episodes_count(self, obj):
        return obj.episodes.count()


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'get_series',
        'season',
        'created_at'
    ]
    list_filter = [
        'season__series',
        'season',
        'created_at'
    ]
    search_fields = [
        'title',
        'title_fr',
        'title_es',
        'season__season_name',
        'season__series__name',
        'file_uuid'
    ]
    ordering = ['season', 'title']

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ['file_uuid', 'created_at', 'updated_at']

    @admin.display(description='Series', ordering='season__series__name')
    def get_series(self, obj):
        return obj.season.series.name if obj.season and obj.season.series else "-"


@admin.register(WatchLater)
class WatchLaterAdmin(admin.ModelAdmin):
    list_display = ['user', 'movies_count', 'series_count']
    search_fields = ['user__email', 'user__username', 'user__full_name']
    filter_horizontal = ['movies', 'series']

    @admin.display(description='Saved Movies')
    def movies_count(self, obj):
        return obj.movies.count()

    @admin.display(description='Saved Series')
    def series_count(self, obj):
        return obj.series.count()


@admin.register(PremiumCollection)
class PremiumCollectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'movies_count', 'series_count']
    search_fields = ['user__email', 'user__username', 'user__full_name']
    filter_horizontal = ['movies', 'series']

    @admin.display(description='Premium Movies')
    def movies_count(self, obj):
        return obj.movies.count()

    @admin.display(description='Premium Series')
    def series_count(self, obj):
        return obj.series.count()


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'movies_count', 'series_count']
    search_fields = ['user__email', 'user__username', 'user__full_name']
    filter_horizontal = ['movies', 'series']

    @admin.display(description='Watched Movies')
    def movies_count(self, obj):
        return obj.movies.count()

    @admin.display(description='Watched Series')
    def series_count(self, obj):
        return obj.series.count()


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'movies_count', 'series_count', 'episodes_count']
    search_fields = ['user__email', 'user__username', 'user__full_name']
    filter_horizontal = ['movies', 'series', 'episodes']

    @admin.display(description='Liked Movies')
    def movies_count(self, obj):
        return obj.movies.count()

    @admin.display(description='Liked Series')
    def series_count(self, obj):
        return obj.series.count()

    @admin.display(description='Liked Episodes')
    def episodes_count(self, obj):
        return obj.episodes.count()


@admin.register(DisLike)
class DisLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'movies_count', 'series_count', 'episodes_count']
    search_fields = ['user__email', 'user__username', 'user__full_name']
    filter_horizontal = ['movies', 'series', 'episodes']

    @admin.display(description='Disliked Movies')
    def movies_count(self, obj):
        return obj.movies.count()

    @admin.display(description='Disliked Series')
    def series_count(self, obj):
        return obj.series.count()

    @admin.display(description='Disliked Episodes')
    def episodes_count(self, obj):
        return obj.episodes.count()


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'query']
    ordering = ['-created_at']


@admin.register(VideoProgressStatus)
class VideoProgressStatusAdmin(admin.ModelAdmin):
    list_display = [
        'file_uuid',
        'last_position_seconds',
        'total_duration_seconds',
        'progress_percentage',
        'last_updated'
    ]
    search_fields = ['file_uuid']
    ordering = ['-last_updated']

    @admin.display(description='Progress')
    def progress_percentage(self, obj):
        if obj.total_duration_seconds and obj.total_duration_seconds > 0:
            pct = round((obj.last_position_seconds / obj.total_duration_seconds) * 100, 1)
            return f"{pct}%"
        return "0%"
