import uuid

import boto3
from asgiref.sync import sync_to_async
from botocore.config import Config
from django.conf import settings
from ninja.files import UploadedFile


class S3Service:
    """Service for handling S3/MinIO operations."""

    def __init__(self):
        self.endpoint_url = settings.AWS_S3_ENDPOINT_URL
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = settings.AWS_S3_REGION_NAME
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self._client = None

    @property
    def client(self):
        """Lazy initialization of the S3 client."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region_name,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    async def upload_file(self, file: UploadedFile, folder: str = "uploads") -> str:
        """
        Uploads a file to S3 and returns its public URL.
        """
        try:
            # Generate unique filename
            file_extension = file.name.split(".")[-1] if "." in file.name else "bin"
            filename = f"{folder}/{uuid.uuid4()}.{file_extension}"

            @sync_to_async
            def perform_upload():
                # self.client property will initialize synchronously here
                self._ensure_bucket_exists()
                self.client.upload_fileobj(
                    file,
                    self.bucket_name,
                    filename,
                    ExtraArgs={
                        "ContentType": file.content_type or "application/octet-stream"
                    },
                )

            await perform_upload()
            return self.get_file_url(filename)
        except Exception as e:
            # You might want to log this error or re-raise a custom exception
            raise RuntimeError(f"Failed to upload file to S3: {str(e)}") from e

    def _ensure_bucket_exists(self):
        """Internal helper to check/create bucket."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket_name)

    def get_file_url(self, filename: str) -> str:
        """Generate public URL for a file in S3/MinIO."""
        endpoint = self.endpoint_url.rstrip("/")
        return f"{endpoint}/{self.bucket_name}/{filename}"
