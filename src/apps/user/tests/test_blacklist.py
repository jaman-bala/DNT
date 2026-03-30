from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.services.blacklist_service import BlacklistService

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class BlacklistTestCase(TestCase):
    def setUp(self):
        self.user_data = {
            "phone": "+996500000000",
            "email": "test@example.com",
            "password": "testpass123",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_logout_blacklists_token(self):
        # 1. Login to get tokens
        login_data = {"phone": "+996500000000", "password": "testpass123"}
        response = self.client.post(
            "/api/v1/auth/login", data=login_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        access_token = response.json()["access"]

        # 2. Verify access to /me
        response = self.client.get(
            "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 200)

        # 3. Logout
        response = self.client.post(
            "/api/v1/auth/logout", HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 200)

        # 4. Verify /me is now unauthorized with the same token
        response = self.client.get(
            "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token validation failed", response.content.decode())

    def test_manual_blacklist_check(self):
        refresh = RefreshToken.for_user(self.user)
        jti = refresh["jti"]
        exp = refresh.payload["exp"]

        self.assertFalse(BlacklistService.is_blacklisted(jti))

        BlacklistService.add_to_blacklist(jti, exp)

        self.assertTrue(BlacklistService.is_blacklisted(jti))
