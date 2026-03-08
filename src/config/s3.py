import boto3
from botocore.config import Config
from django.conf import settings


class S3Client:
    """Singleton-like S3 client helper."""

    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                config=Config(signature_version="s3v4"),
            )
        return cls._client

    @staticmethod
    def get_file_url(filename: str) -> str:
        """Generate public URL for a file in S3/MinIO."""
        # Clean endpoint URL from trailing slash
        endpoint = settings.AWS_S3_ENDPOINT_URL.rstrip("/")
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        return f"{endpoint}/{bucket}/{filename}"
