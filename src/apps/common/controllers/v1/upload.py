from typing import Literal

from django.conf import settings
from ninja import File, Router
from ninja.files import UploadedFile
from pydantic import BaseModel, Field

from apps.common.utils.ratelimit import enforce_rate_limit
from apps.user.exceptions import FileUploadError
from config.auth.authentication import UnifiedJWTAuthentication
from config.container import container

router = Router(tags=["Common Upload"])

# Extension -> accepted Content-Type(s). Extend alongside
# settings.ALLOWED_UPLOAD_EXTENSIONS when your own models need other file types.
EXTENSION_CONTENT_TYPES: dict[str, set[str]] = {
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "webp": {"image/webp"},
    "pdf": {"application/pdf"},
}

UploadFolder = Literal["avatars", "documents", "uploads"]


class UploadResponse(BaseModel):
    url: str = Field(..., description="Uploaded file URL")


def _validate_upload(file: UploadedFile) -> str:
    """Validate size/extension/content-type, returning the lowercased extension."""
    if file.size is not None and file.size > settings.MAX_UPLOAD_SIZE:
        raise FileUploadError(
            f"File too large: max {settings.MAX_UPLOAD_SIZE} bytes allowed"
        )

    extension = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
    if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise FileUploadError(f"File extension '.{extension}' is not allowed")

    allowed_content_types = EXTENSION_CONTENT_TYPES.get(extension)
    if not allowed_content_types or file.content_type not in allowed_content_types:
        raise FileUploadError(
            f"Content-Type '{file.content_type}' does not match extension '.{extension}'"
        )

    return extension


@router.post("/upload", response=UploadResponse, auth=UnifiedJWTAuthentication())
async def upload_file(
    request,
    file: UploadedFile = File(...),
    folder: UploadFolder = "uploads",
):
    """
    Universal endpoint to upload files to S3/MinIO and get a URL.
    """
    await enforce_rate_limit(
        request,
        scope="upload",
        limit=20,
        window_seconds=600,
        extra_key=str(request.user.id),
    )

    _validate_upload(file)

    url = await container.s3_service.upload_file(file, folder=folder)
    return {"url": url}
