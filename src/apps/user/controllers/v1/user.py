import uuid

from ninja import File, Form, Query, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.pagination import paginate

from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserResponseDTO,
    UserUpdateFormDataDTO,
)
from apps.user.filters import UserFilterSchema
from config.auth.authentication import UnifiedJWTAuthentication
from config.container import container
from config.pagination import CustomPagination

router = Router(tags=["User"])


@router.put("/me_update", response=UserResponseDTO, auth=UnifiedJWTAuthentication())
async def update_current_user(
    request,
    email: str | None = Form(None),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    profile_image: UploadedFile | None = File(None),
):
    profile_image_url = None
    if profile_image:
        profile_image_url = await container.s3_service.upload_file(
            profile_image, folder="profile_images"
        )

    data = UserUpdateFormDataDTO(
        email=email,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
    )
    user = await container.user_service.update_user_with_file(
        request.user, data, profile_image_url=profile_image_url
    )
    return user


@router.get("/", response=list[UserResponseDTO], auth=UnifiedJWTAuthentication())
@paginate(CustomPagination)
async def list_users(
    request,
    filters: UserFilterSchema = Query(...),
):
    if not request.user.is_staff:
        raise HttpError(403, "Admin access required")

    return await container.user_service.get_all_users(filters=filters)


@router.post("/change_password", auth=UnifiedJWTAuthentication())
async def change_password(
    request,
    data: ChangePasswordDTO,
):
    await container.user_service.change_password(request.user, data)
    return {"detail": "Password changed successfully"}


@router.post("{user_id}/change_password", auth=UnifiedJWTAuthentication())
async def change_user_password(
    request,
    user_id: uuid.UUID,
    data: ChangePasswordDTO,
):
    if not request.user.is_staff:
        raise HttpError(403, "Admin access required")
    user = await container.user_service.get_user_by_id(user_id)
    await container.user_service.change_password(user, data)
    return {"detail": "Password changed successfully"}
