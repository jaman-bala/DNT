from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from ninja import File, Form, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.dto.schemas import (
    LoginRequestDTO,
    LoginResponseDTO,
    RefreshRequestDTO,
    RefreshResponseDTO,
    UserFormDataDTO,
    UserResponseDTO,
)
from apps.user.services.user_service import UserService
from apps.user.utils.password import is_password_change_required
from config.auth.authentication import UnifiedJWTAuthentication

router = Router(tags=["Authentication and Authorization"])


@router.post("/register", response=UserResponseDTO)
def register_user(
    request,
    phone: str = Form(...),
    email: str | None = Form(None),
    password: str = Form(...),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    middle_name: str | None = Form(None),
    profile_image: UploadedFile | None = File(None),
):
    """Register a new user with form data and optional profile image"""
    try:
        data = UserFormDataDTO(
            phone=phone,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )
        user = UserService.create_user_with_file(data, profile_image)
        response = UserResponseDTO.model_validate(user)
        response.password_change_required = is_password_change_required(user)
        return response
    except ValueError as e:
        raise HttpError(400, str(e)) from e


@router.post("/login", response=LoginResponseDTO)
def login(request, data: LoginRequestDTO):
    """Login user and return JWT tokens"""
    user = authenticate(username=data.phone, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")

    if not user.is_active:
        raise HttpError(401, "User account is disabled")

    refresh = RefreshToken.for_user(user)
    # Ensure the token contains the UUID as string
    refresh["user_id"] = str(user.id)
    return LoginResponseDTO(
        access=str(refresh.access_token),
        refresh=str(refresh),
        password_change_required=is_password_change_required(user),
    )


@router.post("/refresh", response=RefreshResponseDTO)
def refresh_token(request, data: RefreshRequestDTO):
    """Refresh access token using refresh token"""
    try:
        refresh_token = RefreshToken(data.refresh)
        # Ensure the token contains the UUID as string
        refresh_token["user_id"] = str(refresh_token.payload.get("user_id"))

        # Generate new access token
        new_access_token = refresh_token.access_token

        return RefreshResponseDTO(access=str(new_access_token))
    except Exception as e:
        raise HttpError(401, f"Invalid refresh token: {str(e)}") from e


@router.get("/me", response=UserResponseDTO, auth=UnifiedJWTAuthentication())
def get_current_user(request):
    """Get current authenticated user"""
    user = request.user
    response = UserResponseDTO.model_validate(user)
    response.password_change_required = is_password_change_required(user)
    return response


@router.post("/logout")
def logout(request):
    """Logout user and clear cookies"""
    response = JsonResponse({"message": "Successfully logged out"})

    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])

    return response
