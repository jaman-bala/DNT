from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.utils.tokens import (
    EMAIL_VERIFICATION_TOKEN_LIFETIME,
    generate_action_token,
)
from config.container import container

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class ResendVerificationTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000040",
            email="verify-me@example.com",
            password="testpass123",
        )
        self.no_email_user = User.objects.create_user(
            phone="+996500000041",
            password="testpass123",
        )

    def _auth_header(self, user):
        access = RefreshToken.for_user(user).access_token
        return f"Bearer {access}"

    def test_resend_requires_auth(self):
        response = self.client.post("/api/v1/auth/email/verify/resend")
        self.assertEqual(response.status_code, 401)

    def test_resend_enqueues_job(self):
        with patch.object(
            container.queue_service, "enqueue", new=AsyncMock()
        ) as mock_enqueue:
            response = self.client.post(
                "/api/v1/auth/email/verify/resend",
                HTTP_AUTHORIZATION=self._auth_header(self.user),
            )

        self.assertEqual(response.status_code, 200)
        mock_enqueue.assert_awaited_once()
        job_name, user_id, _token = mock_enqueue.call_args.args
        self.assertEqual(job_name, "send_verification_email")
        self.assertEqual(user_id, str(self.user.id))

    def test_resend_without_email_on_file_fails(self):
        response = self.client.post(
            "/api/v1/auth/email/verify/resend",
            HTTP_AUTHORIZATION=self._auth_header(self.no_email_user),
        )
        self.assertEqual(response.status_code, 400)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class ConfirmVerificationTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000042",
            email="verify-me2@example.com",
            password="testpass123",
        )

    def _token(self):
        return generate_action_token(
            self.user, "email_verification", EMAIL_VERIFICATION_TOKEN_LIFETIME
        )

    def test_confirm_sets_email_verified(self):
        response = self.client.post(
            "/api/v1/auth/email/verify/confirm",
            data={"token": self._token()},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_token_cannot_be_reused(self):
        token = self._token()

        first = self.client.post(
            "/api/v1/auth/email/verify/confirm",
            data={"token": token},
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            "/api/v1/auth/email/verify/confirm",
            data={"token": token},
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 400)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class EmailChangeResetsVerificationTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000043",
            email="original@example.com",
            password="testpass123",
        )
        self.user.email_verified = True
        self.user.save(update_fields=["email_verified"])

    def test_changing_email_resets_verified_flag(self):
        access = RefreshToken.for_user(self.user).access_token

        response = self.client.patch(
            "/api/v1/users/me_update",
            data={"email": "new-address@example.com"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new-address@example.com")
        self.assertFalse(self.user.email_verified)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class RequireEmailVerificationLoginGateTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.verified_user = User.objects.create_user(
            phone="+996500000044",
            email="verified@example.com",
            password="testpass123",
        )
        self.verified_user.email_verified = True
        self.verified_user.save(update_fields=["email_verified"])

        self.unverified_user = User.objects.create_user(
            phone="+996500000045",
            email="unverified@example.com",
            password="testpass123",
        )

        self.no_email_user = User.objects.create_user(
            phone="+996500000046",
            password="testpass123",
        )

    def _login(self, phone):
        return self.client.post(
            "/api/v1/auth/login",
            data={"phone": phone, "password": "testpass123"},
            content_type="application/json",
        )

    def test_login_unaffected_by_default(self):
        response = self._login("+996500000045")
        self.assertEqual(response.status_code, 200)

    @override_settings(REQUIRE_EMAIL_VERIFICATION=True)
    def test_unverified_email_blocks_login_when_enforced(self):
        response = self._login("+996500000045")
        self.assertEqual(response.status_code, 403)

    @override_settings(REQUIRE_EMAIL_VERIFICATION=True)
    def test_verified_email_still_logs_in_when_enforced(self):
        response = self._login("+996500000044")
        self.assertEqual(response.status_code, 200)

    @override_settings(REQUIRE_EMAIL_VERIFICATION=True)
    def test_no_email_user_is_not_blocked_when_enforced(self):
        response = self._login("+996500000046")
        self.assertEqual(response.status_code, 200)
