from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class UploadEndpointTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="+996500000020", password="testpass123"
        )
        access = RefreshToken.for_user(self.user).access_token
        self.auth_header = f"Bearer {access}"

    def test_anonymous_upload_is_rejected(self):
        file = SimpleUploadedFile("photo.jpg", b"fake-jpeg", content_type="image/jpeg")
        response = self.client.post("/api/v1/common/upload", data={"file": file})
        self.assertEqual(response.status_code, 401)

    def test_disallowed_extension_is_rejected(self):
        file = SimpleUploadedFile(
            "payload.exe", b"MZ...", content_type="application/octet-stream"
        )
        response = self.client.post(
            "/api/v1/common/upload",
            data={"file": file},
            HTTP_AUTHORIZATION=self.auth_header,
        )
        self.assertEqual(response.status_code, 400)

    def test_content_type_spoofing_is_rejected(self):
        """An .html file renamed with an image extension must still be caught
        by the Content-Type check, not just the extension allowlist."""
        file = SimpleUploadedFile(
            "innocent.jpg", b"<script>alert(1)</script>", content_type="text/html"
        )
        response = self.client.post(
            "/api/v1/common/upload",
            data={"file": file},
            HTTP_AUTHORIZATION=self.auth_header,
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(MAX_UPLOAD_SIZE=10)
    def test_oversized_file_is_rejected(self):
        file = SimpleUploadedFile("photo.jpg", b"x" * 1024, content_type="image/jpeg")
        response = self.client.post(
            "/api/v1/common/upload",
            data={"file": file},
            HTTP_AUTHORIZATION=self.auth_header,
        )
        self.assertEqual(response.status_code, 400)

    def test_valid_upload_succeeds(self):
        file = SimpleUploadedFile("photo.jpg", b"fake-jpeg", content_type="image/jpeg")

        with patch(
            "apps.common.services.s3_service.S3Service.upload_file",
            new=AsyncMock(return_value="http://minio/media/uploads/photo.jpg"),
        ):
            response = self.client.post(
                "/api/v1/common/upload",
                data={"file": file},
                HTTP_AUTHORIZATION=self.auth_header,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["url"], "http://minio/media/uploads/photo.jpg")
