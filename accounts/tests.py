from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase
from accounts.models import CustomUser
from accounts.admin import CustomUserAdmin
from movie_series.models import Movie, Series


class GuestLoginTests(APITestCase):
    def test_guest_login_creates_user_and_returns_tokens(self):
        url = reverse('guest_login')
        payload = {
            'device_id': 'e4b3c2a1-d9e8-47c6-b5a4-f3e2d1c0b9a8',
            'push_token': 'fcm_token_xyz_123...',
            'platform': 'android',
            'model': 'Pixel 8 Pro',
            'os_version': '14',
            'app_version': '2.1.0',
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertTrue(data['is_new_user'])

        user_model = get_user_model()
        user = user_model.objects.get(username='guest_e4b3c2a1-d9e8-47c6-b5a4-f3e2d1c0b9a8')
        self.assertEqual(user.device_token, 'fcm_token_xyz_123...')
        self.assertEqual(user.platform, 'android')
        self.assertEqual(user.device_model, 'Pixel 8 Pro')
        self.assertEqual(user.os_version, '14')
        self.assertEqual(user.app_version, '2.1.0')


class CustomUserAdminViewCountTests(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.user = CustomUser.objects.create_user(
            email="testadminuser@example.com",
            password="password123",
            username="testadminuser"
        )
        self.movie1 = Movie.objects.create(title="Movie 1", publish=True)
        self.movie2 = Movie.objects.create(title="Movie 2", publish=True)
        self.series1 = Series.objects.create(name="Series 1")

    def test_user_admin_view_counts(self):
        self.user.watch_history.movies.add(self.movie1, self.movie2)
        self.user.watch_history.series.add(self.series1)

        user_admin = CustomUserAdmin(CustomUser, self.site)
        request = self.factory.get('/admin/accounts/customuser/')
        request.user = self.user
        qs = user_admin.get_queryset(request)
        annotated_user = qs.get(id=self.user.id)

        self.assertEqual(annotated_user.annotated_movies_count, 2)
        self.assertEqual(annotated_user.annotated_series_count, 1)
        self.assertEqual(annotated_user.annotated_total_views, 3)

        self.assertEqual(user_admin.watched_movies_count(annotated_user), 2)
        self.assertEqual(user_admin.watched_series_count(annotated_user), 1)
        self.assertEqual(user_admin.total_view_count(annotated_user), 3)

        summary = user_admin.user_watch_summary(self.user)
        self.assertIn("2 Movies watched, 1 Series watched (Total: 3 views)", summary)


from unittest.mock import patch
from accounts.models import SiteConfig, ScholarshipApplicant

class ScholarshipApplicantVerificationTests(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(email="user1@example.com", password="password123", username="user1")
        self.user2 = CustomUser.objects.create_user(email="user2@example.com", password="password123", username="user2")
        self.user3 = CustomUser.objects.create_user(email="user3@example.com", password="password123", username="user3")

    @patch("accounts.signals.send_mail")
    def test_admin_check_true_sends_email_to_all_users(self, mock_send_mail):
        site_config, _ = SiteConfig.objects.get_or_create(id=1, defaults={"admin_check": True})
        site_config.admin_check = True
        site_config.save()

        applicant = ScholarshipApplicant.objects.create(user=self.user1, admin_verified=False)
        applicant.admin_verified = True
        applicant.save()

        # Check mock_send_mail call
        self.assertTrue(mock_send_mail.called)
        kwargs = mock_send_mail.call_args[1] if mock_send_mail.call_args[1] else mock_send_mail.call_args.kwargs
        recipients = kwargs.get("recipient_list", [])
        self.assertIn("user1@example.com", recipients)
        self.assertIn("user2@example.com", recipients)
        self.assertIn("user3@example.com", recipients)
        self.assertEqual(len(recipients), 3)

    @patch("accounts.signals.send_mail")
    def test_admin_check_false_sends_email_only_to_single_applicant(self, mock_send_mail):
        site_config, _ = SiteConfig.objects.get_or_create(id=1, defaults={"admin_check": False})
        site_config.admin_check = False
        site_config.save()

        applicant = ScholarshipApplicant.objects.create(user=self.user1, admin_verified=False)
        applicant.admin_verified = True
        applicant.save()

        # Check mock_send_mail call
        self.assertTrue(mock_send_mail.called)
        kwargs = mock_send_mail.call_args[1] if mock_send_mail.call_args[1] else mock_send_mail.call_args.kwargs
        recipients = kwargs.get("recipient_list", [])
        self.assertEqual(recipients, ["user1@example.com"])

