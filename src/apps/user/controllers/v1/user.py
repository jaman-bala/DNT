import uuid

from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserResponseDTO,
    UserUpdateFormDataDTO,
)
from apps.user.exceptions import UserError, UserNotFoundError
from apps.user.filters import UserFilterSchema
from apps.user.services.user_service import UserService
from config.auth.authentication import UnifiedJWTAuthentication
from config.pagination import CustomPagination
from ninja import File, Form, Query, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.pagination import paginate

router = Router(tags=["User"])


@router.put("/me", response=UserResponseDTO, auth=UnifiedJWTAuthentication())
def update_current_user(
    request,
    email: str | None = Form(None),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    profile_image: UploadedFile | None = File(None),
):
    """Update current user profile with form data and optional profile image upload"""
    try:
        data = UserUpdateFormDataDTO(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )
        user = UserService().update_user_with_file(request.user, data, profile_image)
        return user
    except UserError as e:
        raise HttpError(400, str(e)) from e
    except Exception as e:
        raise HttpError(500, f"Internal server error: {str(e)}") from e


@router.get("/", response=list[UserResponseDTO], auth=UnifiedJWTAuthentication())
@paginate(CustomPagination)
def list_users(request, filters: UserFilterSchema = Query(...)):
    """List all users (admin only)"""
    if not request.user.is_staff:
        raise HttpError(403, "Admin access required")

    return UserService().get_all_users(filters=filters)


@router.post("change-password", auth=UnifiedJWTAuthentication())
def change_password(
    request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Change current user's password"""
    try:
        data = ChangePasswordDTO(
            new_password=new_password, confirm_password=confirm_password
        )
        UserService().change_password(request.user, data)
        return {"detail": "Password changed successfully"}
    except UserError as e:
        raise HttpError(400, str(e)) from e
    except Exception as e:
        raise HttpError(500, f"Internal server error: {str(e)}") from e


@router.post("{user_id}/change-password", auth=UnifiedJWTAuthentication())
def change_user_password(
    request,
    user_id: uuid.UUID,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Change user's password by ID (admin only)"""
    if not request.user.is_staff:
        raise HttpError(403, "Admin access required")

    try:
        service = UserService()
        user = service.get_user_by_id(user_id)
        data = ChangePasswordDTO(
            new_password=new_password, confirm_password=confirm_password
        )
        service.change_password(user, data)
        return {"detail": "Password changed successfully"}
    except UserNotFoundError as e:
        raise HttpError(404, str(e)) from e
    except UserError as e:
        raise HttpError(400, str(e)) from e
    except Exception as e:
        raise HttpError(500, f"Internal server error: {str(e)}") from e
