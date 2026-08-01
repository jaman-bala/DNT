from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.user.utils.tokens import PASSWORD_RESET_TOKEN_LIFETIME, generate_action_token
from config.container import container

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class PasswordResetRequestTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000030",
            email="reset-me@example.com",
            password="oldpass123",
        )

    def test_request_with_existing_email_enqueues_job(self):
        with patch.object(
            container.queue_service, "enqueue", new=AsyncMock()
        ) as mock_enqueue:
            response = self.client.post(
                "/api/v1/auth/password-reset/request",
                data={"email": "reset-me@example.com"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        mock_enqueue.assert_awaited_once()
        job_name, user_id, _token = mock_enqueue.call_args.args
        self.assertEqual(job_name, "send_password_reset_email")
        self.assertEqual(user_id, str(self.user.id))

    def test_request_with_unknown_email_is_silently_a_no_op(self):
        """No account enumeration: same response, no job enqueued."""
        with patch.object(
            container.queue_service, "enqueue", new=AsyncMock()
        ) as mock_enqueue:
            response = self.client.post(
                "/api/v1/auth/password-reset/request",
                data={"email": "nobody@example.com"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        mock_enqueue.assert_not_awaited()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class PasswordResetConfirmTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000031",
            email="reset-me2@example.com",
            password="oldpass123",
        )

    def _token(self):
        return generate_action_token(
            self.user, "password_reset", PASSWORD_RESET_TOKEN_LIFETIME
        )

    def test_confirm_with_valid_token_changes_password(self):
        token = self._token()

        response = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            data={
                "token": token,
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        login = self.client.post(
            "/api/v1/auth/login",
            data={"phone": "+996500000031", "password": "newpass123"},
            content_type="application/json",
        )
        self.assertEqual(login.status_code, 200)

    def test_confirm_rejects_mismatched_passwords(self):
        token = self._token()

        response = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            data={
                "token": token,
                "new_password": "newpass123",
                "confirm_password": "different123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_token_cannot_be_reused(self):
        token = self._token()

        first = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            data={
                "token": token,
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            data={
                "token": token,
                "new_password": "anotherpass123",
                "confirm_password": "anotherpass123",
            },
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 400)

    def test_confirm_with_garbage_token_fails(self):
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            data={
                "token": "not-a-real-token",
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_access_token_cannot_be_used_as_reset_token(self):
        """token_type mismatch: an access token must not work here either."""
        from rest_framework_simplejwt.tokens import RefreshToken

        access_token = str(RefreshToken.for_user(self.user).access_token)

        response = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            data={
                "token": access_token,
                "new_password": "newpass123",
                "confirm_password": "newpass123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
