from django.contrib import admin
from .models import (
    Genre, Movie, Series,
    Season, Episode, WatchHistory,
    PremiumCollection, Like, DisLike
)

# from .forms import MovieFileUploadForm


@admin.action(description="Mark selected queries as published")
def make_published(modeladmin, request, queryset):
    queryset.update(publish=True)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    search_fields = ['title']

    list_filter = ['release_year']

    actions = [make_published]

    def get_form(self, request, obj, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # return MovieFileUploadForm
        # print(form)
        # form.base_fields['status'].initial = 'UPLOADED'

        # print(form.base_fields['status'])
        if 'upload_video' in form.base_fields.keys():
            form.base_fields.pop('upload_video')
        # print(form.base_fields['status'].__class__)
        # print(form.base_fields)
        return form
        pass

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, b):
        return [
            # 'status',
            'file_uuid',
            'notifyees'
        ]

    # def add_view(self, request, from_url="", extra_context={}):
    #     extra_context = extra_context or {}
    #     extra_context['show_save_and_add_another'] = False
    #     extra_context['show_save_and_continue'] = False

    #     if request.method == 'POST':
    #         print(request.POST)
    #     return super().add_view(request, extra_context=extra_context)
    #     pass

    # def change_view(self, request, object_id, extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['show_save_and_add_another'] = False
    #     extra_context['show_save_and_continue'] = False
    #     return super().change_view(request, object_id, extra_context=extra_context)

    # def save_model(self, request, new_object, form, not_add):
    #     pass
    # pass


# from django.contrib import admin

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0


class SeasonInline(admin.TabularInline):  # Or admin.StackedInline for a different layout
    model = Season
    extra = 0  # Optional: Number of empty forms to display by default (0 = none)
    inlines = [EpisodeInline]
# # class AuthorAdmin(admin.ModelAdmin):
# #     inlines = [BookInline]


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['seasons__release_year']
    inlines = [SeasonInline]

    # def has_add_permission(self, request):
    #     return False


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    actions = [make_published]

    # def has_add_permission(self, request):
    #     return False

    def get_readonly_fields(self, request, b):
        return [
            "notifyees"
        ]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    pass

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, b):
        return ['file_uuid']


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(PremiumCollection)
class PremiumCollectionAdmin(admin.ModelAdmin):
    pass


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    pass


@admin.register(DisLike)
class LikeAdmin(admin.ModelAdmin):
    pass
