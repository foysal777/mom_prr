from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from rest_framework.test import APIClient
from movie_series.models import Movie, Series
from movie_series.admin import MovieAdmin, SeriesAdmin

UserModel = get_user_model()


class ViewCountMeasureTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.user1 = UserModel.objects.create_user(
            email="user1@example.com",
            password="password123",
            username="user1"
        )
        self.user2 = UserModel.objects.create_user(
            email="user2@example.com",
            password="password123",
            username="user2"
        )
        self.movie = Movie.objects.create(
            title="Test Movie",
            publish=True
        )
        self.series = Series.objects.create(
            name="Test Series"
        )
        self.client = APIClient()

    def test_movie_admin_user_views_count(self):
        # User 1 watches movie
        self.user1.watch_history.movies.add(self.movie)

        movie_admin = MovieAdmin(Movie, self.site)
        request = self.factory.get('/admin/movie_series/movie/')
        request.user = self.user1
        qs = movie_admin.get_queryset(request)
        annotated_movie = qs.get(id=self.movie.id)

        self.assertEqual(annotated_movie.annotated_user_views, 1)
        self.assertEqual(movie_admin.user_views_count(annotated_movie), 1)

        # User 2 also watches movie
        self.user2.watch_history.movies.add(self.movie)
        qs = movie_admin.get_queryset(request)
        annotated_movie = qs.get(id=self.movie.id)

        self.assertEqual(annotated_movie.annotated_user_views, 2)
        self.assertEqual(movie_admin.user_views_count(annotated_movie), 2)

    def test_series_admin_user_views_count(self):
        self.user1.watch_history.series.add(self.series)

        series_admin = SeriesAdmin(Series, self.site)
        request = self.factory.get('/admin/movie_series/series/')
        request.user = self.user1
        qs = series_admin.get_queryset(request)
        annotated_series = qs.get(id=self.series.id)

        self.assertEqual(annotated_series.annotated_user_views, 1)
        self.assertEqual(series_admin.user_views_count(annotated_series), 1)

    def test_movie_detail_view_increments_per_user_only_once(self):
        self.client.force_authenticate(user=self.user1)
        url = f"/movie_and_series/movie/{self.movie.id}/detail/"

        # First request should increment view_count
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.view_count, 1)
        self.assertTrue(self.user1.watch_history.movies.filter(id=self.movie.id).exists())

        # Second request from same user should NOT increment view_count again
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.view_count, 1)

        # Request from second user SHOULD increment view_count to 2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.view_count, 2)
        self.assertTrue(self.user2.watch_history.movies.filter(id=self.movie.id).exists())

    def test_series_detail_view_increments_per_user_only_once(self):
        self.client.force_authenticate(user=self.user1)
        url = f"/movie_and_series/series/{self.series.id}/detail/"

        # First request should increment view_count
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.series.refresh_from_db()
        self.assertEqual(self.series.view_count, 1)
        self.assertTrue(self.user1.watch_history.series.filter(id=self.series.id).exists())

        # Second request from same user should NOT increment view_count again
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.series.refresh_from_db()
        self.assertEqual(self.series.view_count, 1)

        # Request from second user SHOULD increment view_count to 2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.series.refresh_from_db()
        self.assertEqual(self.series.view_count, 2)
        self.assertTrue(self.user2.watch_history.series.filter(id=self.series.id).exists())
