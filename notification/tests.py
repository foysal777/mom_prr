from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Device

User = get_user_model()


class DeviceRegistrationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            username="testuser"
        )
        self.client.force_authenticate(user=self.user)
        self.register_url = "/notification/device/register/"

    def test_register_device_success(self):
        payload = {
            "device_id": "e4b3c2a1-d9e8-47c6-b5a4-f3e2d1c0b9a8",
            "push_token": "fcm_token_xyz_123...",
            "platform": "android",
            "model": "Pixel 8 Pro",
            "os_version": "14",
            "app_version": "2.1.0"
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Verify device object was created in database
        device = Device.objects.get(device_id="e4b3c2a1-d9e8-47c6-b5a4-f3e2d1c0b9a8")
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.push_token, "fcm_token_xyz_123...")
        self.assertEqual(device.platform, "android")
        self.assertEqual(device.model, "Pixel 8 Pro")
        self.assertEqual(device.os_version, "14")
        self.assertEqual(device.app_version, "2.1.0")

        # Verify CustomUser.device_token was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.device_token, "fcm_token_xyz_123...")

    def test_register_device_missing_fields(self):
        payload = {
            "device_id": "e4b3c2a1-d9e8-47c6-b5a4-f3e2d1c0b9a8"
            # missing platform and push_token
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
