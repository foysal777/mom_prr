import os

import datetime
# catalog/models.py
from decimal import Decimal
from django.db import models, transaction
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.models import Case, When, Value, Q


UserModel = get_user_model()


def get_upload_to(instance, filename):
    return os.path.join('uploads', f"{instance.id}_{filename}")


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(TimeStamped):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["name"])]

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*a, **kw)

    def __str__(self): return self.name

    @staticmethod
    def get_or_create_genres_safe(slug_list):
        """
        Safe version with error handling and transaction
        """
        genres = []

        with transaction.atomic():
            for slug in slug_list:
                try:
                    genre = Genre.objects.get(slug=slug)
                    genres.append(genre)
                except Genre.DoesNotExist:
                    name = slug.replace('-', ' ').replace('_', ' ').title()
                    try:
                        genre = Genre.objects.create(slug=slug, name=name)
                        genres.append(genre)
                    except Exception as e:
                        print(f"Error creating genre {slug}: {e}")
                        continue

        return genres


def get_default_year():
    return datetime.datetime.now().year


class CommonMovieSeriesManager(models.Manager):
    def get_queryset(self):
        # print('MODEL NAME', self.model.__name__)
        qs = super().get_queryset()
        qs = qs.annotate(
            is_premium=Case(
                When(
                    Q(premium_price_usd__gt=0)
                    | Q(premium_price_gourde__gt=0),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=models.BooleanField(),
            )
        )
        return qs


def generate_gif_path(instance, filename):
    return str(settings.MEDIA_ROOT/f"{uuid.uuid4()}_{filename}")


class Movie(TimeStamped):
    title = models.CharField(max_length=255, db_index=True)
    title_fr = models.CharField(max_length=255, db_index=True, default="")
    title_es = models.CharField(max_length=255, db_index=True, default="")

    description = models.TextField(default="", blank=True)
    description_fr = models.TextField(default="", blank=True)
    description_es = models.TextField(default="", blank=True)
    release_year = models.PositiveIntegerField(
        db_index=True,
        default=get_default_year
    )

    comming_soon_time = models.DateField(null=True, blank=True)
    runtime_minutes = models.PositiveIntegerField(null=True, blank=True)
    genres = models.ManyToManyField("Genre", related_name="movies", blank=True)
    file_uuid = models.TextField(null=True, blank=True)
    preview_gif = models.FileField(null=True, blank=True)
    trailer = models.FileField(null=True, blank=True, upload_to=get_upload_to)

    posters_url = models.JSONField(default=list, blank=True)
    is_popular = models.BooleanField(default=False)
    premium_price_usd = models.DecimalField(
        default=0.0,
        max_digits=5,
        decimal_places=2
    )
    premium_price_gourde = models.DecimalField(
        default=0.0,
        max_digits=5,
        decimal_places=2
    )
    view_count = models.PositiveIntegerField(default=0)
    publish = models.BooleanField(default=False)

    objects = CommonMovieSeriesManager()

    notifyees = models.JSONField(default=list)

    class Meta:
        indexes = [
            models.Index(fields=["release_year"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title

    @property
    def likes(self):
        return len(self.like_set.all())

    @property
    def dislikes(self):
        return len(self.dislike_set.all())

    def get_name(self):
        return self.title


class Series(TimeStamped):
    name = models.CharField(
        max_length=255, db_index=True, unique=True
    )
    name_fr = models.CharField(
        max_length=255, db_index=True, default=""
    )
    name_es = models.CharField(
        max_length=255, db_index=True, default=""
    )
    # is_published = models.BooleanField(default=True, db_index=True)
    description = models.TextField(default="", blank=True)
    description_fr = models.TextField(default="", blank=True)
    description_es = models.TextField(default="", blank=True)
    genres = models.ManyToManyField(
        "Genre", related_name="series_set", blank=True
    )
    premium_price_usd = models.DecimalField(
        default=0.0,
        max_digits=5,
        decimal_places=2
    )
    premium_price_gourde = models.DecimalField(
        default=0.0,
        max_digits=5,
        decimal_places=2
    )

    is_popular = models.BooleanField(default=False)
    posters_url = models.JSONField(default=list, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    objects = CommonMovieSeriesManager()

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]
        pass

    def __str__(self): return self.name

    @property
    def likes(self):
        return len(self.like_set.all())

    @property
    def dislikes(self):
        return len(self.dislike_set.all())




class SeasonManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()

        qs.select_related('series')
        return qs


class Season(TimeStamped):
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="seasons",
        db_index=True
    )
    release_year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    comming_soon_time = models.DateField(null=True, blank=True)

    publish = models.BooleanField(default=False)
    season_name = models.TextField(db_index=True, default="")

    notifyees = models.JSONField(default=list)

    objects = SeasonManager()

    class Meta:
        unique_together = (("series", "season_name"),)
        indexes = [models.Index(fields=["series", "season_name"])]

    def __str__(self):
        return f"{self.series.name} S{self.season_name}"

    def get_name(self):
        return self.season_name


class Episode(TimeStamped):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="episodes", db_index=True)
    # number = models.PositiveIntegerField(db_index=True)
    title = models.CharField(max_length=255, blank=True, default="")
    title_fr = models.CharField(max_length=255, blank=True, default="")
    title_es = models.CharField(max_length=255, blank=True, default="")
    file_uuid = models.TextField(blank=True, null=True)
    trailer = models.FileField(blank=True, null=True, upload_to=get_upload_to)

    class Meta:
        unique_together = (("season", "title"),)
        indexes = [models.Index(fields=["season"])]

    def __str__(self):
        return f"{self.season.series.name} S{self.season.season_name} E{self.title}"

    def get_file(self):
        return self.file_path

    def is_premium(self):
        return self.season.series.is_premium

    def is_premium_collection(self, user):
        assert isinstance(user, UserModel)
        return self.season.series in user.premium_collection.series

    @property
    def likes(self):
        return len(self.like_set.all())

    @property
    def dislikes(self):
        return len(self.dislike_set.all())


class WatchLater(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE,
        related_name='watch_later'
    )
    movies = models.ManyToManyField(Movie)
    series = models.ManyToManyField(Series)


class PremiumCollection(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE,
        related_name='premium_collection'
    )

    movies = models.ManyToManyField(Movie, blank=True)
    series = models.ManyToManyField(Series, blank=True)

    def __str__(self):
        return str(self.user.get_full_name)


class SearchHistory(models.Model):
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE,
        related_name='search_history'
    )
    query = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    MAX_ROWS_PER_USER = 10

    class Meta:
        ordering = ['-created_at']
        indexes = [
           models.Index(fields=['user', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        user_records = self.__class__.objects.filter(user=self.user)
        if user_records.count() > self.MAX_ROWS_PER_USER:
            excess_count = user_records.count() - self.MAX_ROWS_PER_USER
            oldest_records = user_records.order_by('created_at')[:excess_count]
            oldest_ids = list(oldest_records.values_list('id', flat=True))
            self.__class__.objects.filter(id__in=oldest_ids).delete()


class WatchHistory(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE,
        related_name='watch_history'
    )

    movies = models.ManyToManyField(Movie, blank=True)
    series = models.ManyToManyField(Series, blank=True)


class Like(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE,
        related_name='likes'
    )
    movies = models.ManyToManyField(Movie, blank=True)
    series = models.ManyToManyField(Series, blank=True)
    episodes = models.ManyToManyField(Episode, blank=True)


class DisLike(models.Model):
    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE,
        related_name='dislikes'
    )
    movies = models.ManyToManyField(Movie, blank=True)
    series = models.ManyToManyField(Series, blank=True)
    episodes = models.ManyToManyField(Episode, blank=True)


class VideoProgressStatus(models.Model):
    file_uuid = models.CharField(max_length=100, unique=True)
    last_position_seconds = models.IntegerField()
    total_duration_seconds = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)