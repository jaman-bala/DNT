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
from apps.user.services.blacklist_service import BlacklistService
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
    data = UserFormDataDTO(
        phone=phone,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
    )
    user = UserService().create_user(data, profile_image)
    return user


@router.post("/login", response=LoginResponseDTO)
def login(request, data: LoginRequestDTO):
    user = authenticate(username=data.phone, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")

    if not user.is_active:
        raise HttpError(401, "User account is disabled")

    refresh = RefreshToken.for_user(user)
    refresh["user_id"] = str(user.id)
    return LoginResponseDTO(
        access=str(refresh.access_token),
        refresh=str(refresh),
        password_change_required=is_password_change_required(user),
    )


@router.post("/refresh", response=RefreshResponseDTO)
def refresh_token(request, data: RefreshRequestDTO):
    try:
        refresh_token = RefreshToken(data.refresh)
        refresh_token["user_id"] = str(refresh_token.payload.get("user_id"))
        new_access_token = refresh_token.access_token

        return RefreshResponseDTO(access=str(new_access_token))
    except Exception as e:
        raise HttpError(401, f"Invalid refresh token: {str(e)}") from e


@router.get("/me", response=UserResponseDTO, auth=UnifiedJWTAuthentication())
def get_current_user(request):
    return request.user


@router.post("/logout", auth=UnifiedJWTAuthentication())
def logout(request):
    access_token_str = request.auth
    if access_token_str:
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            access_token = AccessToken(access_token_str)
            BlacklistService.add_to_blacklist(
                access_token["jti"], access_token.payload["exp"]
            )
        except Exception:
            pass

    refresh_token_str = request.COOKIES.get(
        settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
    )
    if refresh_token_str:
        try:
            from rest_framework_simplejwt.tokens import RefreshToken

            refresh_token = RefreshToken(refresh_token_str)
            BlacklistService.add_to_blacklist(
                refresh_token["jti"], refresh_token.payload["exp"]
            )
        except Exception:
            pass

    response = JsonResponse({"message": "Successfully logged out"})

    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])

    return response
