# catalog/filters.py
import django_filters as df
from django.db.models import Count, Q
from .models import Movie, Series


class _BaseTitleFilter(df.FilterSet):
    q = df.CharFilter(method="filter_q", help_text="Case-insensitive title search.")
    year_from = df.NumberFilter(field_name="year", lookup_expr="gte")
    year_to = df.NumberFilter(field_name="year", lookup_expr="lte")
    genres = df.CharFilter(method="filter_genres", help_text="CSV of genre slugs.")
    match = df.ChoiceFilter(
        choices=(
            ("any", "any"),
            ("all", "all")
        ),
        help_text="'any' (default) or 'all'."
    )

    ordering = df.OrderingFilter(
        fields=(
            ("year", "year"),
            ("name", "name"),
            ("created_at", "created_at")
        ),
    )

    def filter_q(self, qs, name, value):
        return qs.filter(name__icontains=value) if value else qs

    def filter_genres(self, qs, name, value):
        if not value:
            return qs
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        if not slugs:
            return qs
        use_all = (self.data.get("match") or "any").lower() == "all"
        if use_all:
            return (qs.filter(genres__slug__in=slugs)
                      .annotate(_m=Count("genres", filter=Q(genres__slug__in=slugs), distinct=True))
                      .filter(_m=len(set(slugs))).distinct())
        return qs.filter(genres__slug__in=slugs).distinct()


class MovieFilter(_BaseTitleFilter):
    class Meta:
        model = Movie
        fields = []


class SeriesFilter(_BaseTitleFilter):
    class Meta:
        model = Series
        fields = []


class SeasonFilter(_BaseTitleFilter):
    class Meta:
        model = Series
        fields = []


