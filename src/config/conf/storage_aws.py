from typing import Any

from config.settings import BASE_DIR
from config.utils import env

USE_AWS = env("USE_AWS", default=False, is_bool=True)

# MinIO settings (always available for file uploads)
AWS_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID", default="minioadmin")
AWS_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY", default="minioadmin")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="http://minio:9000")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="media")


if USE_AWS:
    STATIC_URL = "static/"
    MEDIA_URL = "media/"

    AWS_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID", default="minioadmin")
    AWS_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY", default="minioadmin")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="http://minio:9000")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default=None)
    AWS_S3_USE_SSL = env("AWS_S3_USE_SSL", default=False, is_bool=True)
    AWS_S3_VERIFY = env("AWS_S3_VERIFY", default=False, is_bool=True)
    AWS_S3_URL_PROTOCOL = env("AWS_S3_URL_PROTOCOL", default="http://")

    # MEDIA
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="media")
    S3_URL_EXPIRATION_TIME = env("S3_URL_EXPIRATION_TIME", default=3600)
    AWS_S3_DEFAULT_ACL = env("AWS_S3_DEFAULT_ACL", default="public-read")
    AWS_S3_SIGNATURE_VERSION = env("AWS_S3_SIGNATURE_VERSION", default="s3v4")
    AWS_MEDIA_QUERYSTRING_AUTH = env(
        "AWS_MEDIA_QUERYSTRING_AUTH", default=True, is_bool=True
    )

    # STATIC
    AWS_S3_STATIC_BUCKET_NAME = env("AWS_STORAGE_STATIC_BUCKET_NAME", default="static")
    AWS_S3_STATIC_ACL = env("AWS_S3_STATIC_ACL", default="public-read")
    AWS_S3_STATIC_QUERYSTRING_AUTH = env(
        "AWS_S3_STATIC_QUERYSTRING_AUTH", default=False, is_bool=True
    )
    MINIO_BASE_DOMAIN = env("MINIO_BASE_DOMAIN", default="0.0.0.0:9000")

    AWS_S3_CUSTOM_DOMAIN = env("MINIO_S3_CUSTOM_DOMAIN", default=None)
    STORAGES: dict[str, dict[str, Any]] = {
        # Media file management
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "querystring_auth": AWS_MEDIA_QUERYSTRING_AUTH,
                "signature_version": AWS_S3_SIGNATURE_VERSION,
                "default_acl": AWS_S3_DEFAULT_ACL,
                "querystring_expire": S3_URL_EXPIRATION_TIME,
            },
        },
        # static files management
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": AWS_S3_STATIC_BUCKET_NAME,
                "default_acl": AWS_S3_STATIC_ACL,
                "querystring_auth": AWS_S3_STATIC_QUERYSTRING_AUTH,
            },
        },
    }
    # Enable custom domain for minio storage

    ENABLE_STORAGE_CUSTOM_DOMAIN = env(
        "ENABLE_STORAGE_CUSTOM_DOMAIN", default=False, is_bool=True
    )

    if ENABLE_STORAGE_CUSTOM_DOMAIN:
        STORAGES["default"]["OPTIONS"]["custom_domain"] = (
            f"{MINIO_BASE_DOMAIN}{MEDIA_URL}".rstrip("/")
        )
        STORAGES["staticfiles"]["OPTIONS"]["custom_domain"] = (
            f"{MINIO_BASE_DOMAIN}{STATIC_URL}".rstrip("/")
        )

else:
    STATIC_URL = "/static/"
    STATIC_ROOT = BASE_DIR / "staticfiles"
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL = "/media/"

    STORAGES: dict[str, dict[str, Any]] = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
