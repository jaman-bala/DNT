from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class RefreshTokenCannotAuthenticateTestCase(TestCase):
    """
    Regression test for the fix in config/auth/authentication.py: a refresh
    token must never be accepted as a Bearer access token, even though both
    are signed with the same key and both carry a `user_id` claim.
    """

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000010",
            password="testpass123",
        )

    def _login(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"phone": "+996500000010", "password": "testpass123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_access_token_authenticates(self):
        tokens = self._login()
        response = self.client.get(
            "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
        )
        self.assertEqual(response.status_code, 200)

    def test_refresh_token_is_rejected_as_access_token(self):
        tokens = self._login()
        response = self.client.get(
            "/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {tokens['refresh']}"
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_token_is_rejected_on_logout_endpoint_too(self):
        tokens = self._login()
        response = self.client.post(
            "/api/v1/auth/logout",
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['refresh']}",
        )
        self.assertEqual(response.status_code, 401)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class LoginRateLimitTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000011",
            password="testpass123",
        )

    def test_login_is_rate_limited_after_repeated_failures(self):
        bad_login = {"phone": "+996500000011", "password": "wrongpassword"}

        for _ in range(5):
            response = self.client.post(
                "/api/v1/auth/login", data=bad_login, content_type="application/json"
            )
            self.assertEqual(response.status_code, 401)

        response = self.client.post(
            "/api/v1/auth/login", data=bad_login, content_type="application/json"
        )
        self.assertEqual(response.status_code, 429)
