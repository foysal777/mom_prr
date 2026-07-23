from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


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
