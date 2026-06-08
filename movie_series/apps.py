from django.apps import AppConfig


class MovieSeriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movie_series'

    def ready(self):
        from . import signals
        from .models import Movie

        # from accounts.models import CustomUser
        # print(*[field.name for field in Movie._meta.get_fields()], sep='\n')
        pass