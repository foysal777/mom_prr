from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from rest_framework.test import APIClient
from movie_series.models import Movie, Series, Season
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

    def test_movie_detail_view_contains_all_model_fields(self):
        self.client.force_authenticate(user=self.user1)
        url = f"/movie_and_series/movie/{self.movie.id}/detail/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected_fields = [
            "id", "title", "title_fr", "title_es",
            "description", "description_fr", "description_es",
            "release_year", "runtime_minutes", "comming_soon_time",
            "genres", "file_uuid", "preview_gif", "trailer",
            "poster_url", "posters_url", "is_popular",
            "premium_price_usd", "premium_price_gourde",
            "view_count", "publish", "notifyees", "is_notify",
            "created_at", "updated_at",
            "is_collection", "is_premium", "alias_type",
            "related_movies", "likes", "dislikes",
            "liked", "disliked"
        ]
        for field in expected_fields:
            self.assertIn(field, response.data, f"Field '{field}' missing from movie detail response")

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


class MoviePosterFieldTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.movie = Movie.objects.create(
            title="Poster Test Movie",
            posters_url=["https://example.com/original_vdo_poster.jpg"],
            publish=True
        )
        self.series = Series.objects.create(
            name="Poster Test Series",
            posters_url=["https://example.com/original_series_poster.jpg"]
        )
        self.season = Season.objects.create(
            series=self.series,
            season_name="1",
            publish=True
        )

    def test_movie_poster_url_upload_and_override_posters_url(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from movie_series.serializers import MovieSerializer, MovieDetailSerializer

        # 1x1 transparent PNG
        image_content = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        uploaded_image = SimpleUploadedFile(
            name='test_poster.png',
            content=image_content,
            content_type='image/png'
        )

        self.movie.poster_url = uploaded_image
        self.movie.save()
        self.movie.refresh_from_db()

        self.assertTrue(bool(self.movie.poster_url))
        self.assertIn('test_poster', self.movie.poster_url.name)

        # Verify DB posters_url was overridden with the uploaded poster URL
        self.assertEqual(self.movie.posters_url, [self.movie.poster_url.url])

        # Test MovieAdmin poster_preview
        movie_admin = MovieAdmin(Movie, self.site)
        preview_html = movie_admin.poster_preview(self.movie)
        self.assertIn('<img src="', preview_html)
        self.assertIn(self.movie.poster_url.url, preview_html)

        # Test serializer output overrides posters_url with uploaded poster URL
        serializer_data = MovieSerializer(self.movie).data
        self.assertIn('poster_url', serializer_data)
        self.assertIsNotNone(serializer_data['poster_url'])
        self.assertEqual(serializer_data['posters_url'], [self.movie.poster_url.url])

        detail_serializer_data = MovieDetailSerializer(self.movie).data
        self.assertIn('poster_url', detail_serializer_data)
        self.assertIsNotNone(detail_serializer_data['poster_url'])
        self.assertEqual(detail_serializer_data['posters_url'], [self.movie.poster_url.url])

        # Clean up file
        if self.movie.poster_url:
            self.movie.poster_url.delete(save=False)

    def test_series_and_season_poster_url_upload_and_override(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from movie_series.serializers import SeriesSerializer, SeriesFullSerializer, SeasonSerializer
        from movie_series.admin import SeriesAdmin

        image_content = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        uploaded_image = SimpleUploadedFile(
            name='test_series_poster.png',
            content=image_content,
            content_type='image/png'
        )

        self.series.poster_url = uploaded_image
        self.series.save()
        self.series.refresh_from_db()

        self.assertTrue(bool(self.series.poster_url))
        self.assertIn('test_series_poster', self.series.poster_url.name)

        # Verify DB posters_url was overridden with the uploaded poster URL
        self.assertEqual(self.series.posters_url, [self.series.poster_url.url])

        # Test SeriesAdmin poster_preview
        series_admin = SeriesAdmin(Series, self.site)
        preview_html = series_admin.poster_preview(self.series)
        self.assertIn('<img src="', preview_html)
        self.assertIn(self.series.poster_url.url, preview_html)

        # Test SeriesSerializer and SeriesFullSerializer output
        serializer_data = SeriesSerializer(self.series).data
        self.assertEqual(serializer_data['posters_url'], [self.series.poster_url.url])

        full_serializer_data = SeriesFullSerializer(self.series).data
        self.assertEqual(full_serializer_data['posters_url'], [self.series.poster_url.url])

        # Test SeasonSerializer output overrides posters_url from series
        season_data = SeasonSerializer(self.season).data
        self.assertEqual(season_data['posters_url'], [self.series.poster_url.url])

        # Clean up file
        if self.series.poster_url:
            self.series.poster_url.delete(save=False)

    def test_movie_poster_preview_fallback_to_posters_url(self):
        movie_admin = MovieAdmin(Movie, self.site)
        movie_no_poster = Movie.objects.create(title="No Poster Movie", publish=True)

        # When no poster_url and no posters_url
        self.assertEqual(movie_admin.poster_preview(movie_no_poster), "-")

        # When posters_url has external URLs
        movie_no_poster.posters_url = ["https://example.com/poster1.jpg"]
        movie_no_poster.save()
        preview_html = movie_admin.poster_preview(movie_no_poster)
        self.assertIn('https://example.com/poster1.jpg', preview_html)

