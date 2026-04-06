from ninja import File, Router
from ninja.files import UploadedFile
from pydantic import BaseModel, Field

from config.container import container

router = Router(tags=["Common Upload"])


class UploadResponse(BaseModel):
    url: str = Field(..., description="Uploaded file URL")


@router.post("/upload", response=UploadResponse)
async def upload_file(
    request,
    file: UploadedFile = File(...),
    folder: str = "uploads",
):
    """
    Universal endpoint to upload files to S3/MinIO and get a URL.
    """
    url = await container.s3_service.upload_file(file, folder=folder)
    return {"url": url}
