from ninja import File, Form, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile

from apps.user.dto.schemas import (
    ChangePasswordDTO,
    UserResponseDTO,
    UserUpdateFormDataDTO,
)
from apps.user.models.users import User
from apps.user.services.user_service import UserService
from apps.user.utils.password import is_password_change_required
from config.auth.authentication import UnifiedJWTAuthentication

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
        data = UserUpdateFormDataDTO(email=email, first_name=first_name, last_name=last_name, middle_name=middle_name)
        user = UserService.update_user_with_file(request.user, data, profile_image)
        response = UserResponseDTO.model_validate(user)
        response.password_change_required = is_password_change_required(user)
        return response
    except ValueError as e:
        raise HttpError(400, str(e)) from e


@router.get("/", response=list[UserResponseDTO], auth=UnifiedJWTAuthentication())
def list_users(request):
    """List all users (admin only)"""
    if not request.user.is_staff:
        raise HttpError(403, "Admin access required")

    users = User.objects.all()
    response_list = []
    for user in users:
        dto = UserResponseDTO.model_validate(user)
        dto.password_change_required = is_password_change_required(user)
        response_list.append(dto)
    return response_list


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
        UserService.change_password(request.user, data)
        return {"detail": "Password changed successfully"}
    except ValueError as e:
        raise HttpError(400, str(e)) from e
