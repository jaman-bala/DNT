from django.conf import settings
from django.http import JsonResponse
from ninja import Router

from apps.user.dto.schemas import (
    LoginRequestDTO,
    LoginResponseDTO,
    RefreshRequestDTO,
    RefreshResponseDTO,
    RefreshResponseDTO,
    UserRequestDTO,
    UserResponseDTO,
)
from config.auth.authentication import UnifiedJWTAuthentication
from config.container import container

router = Router(tags=["Authentication and Authorization"])


@router.post("/register", response=UserResponseDTO)
async def register_user(
    request,
    data: UserRequestDTO,
):
    user = await container.user_service.create_user(data)
    return user


@router.post("/login", response=LoginResponseDTO)
async def login(
    request,
    data: LoginRequestDTO,
):
    return await container.auth_service.login(data.phone, data.password)


@router.post("/refresh", response=RefreshResponseDTO)
async def refresh_token(
    request,
    data: RefreshRequestDTO,
):
    return await container.auth_service.refresh_token(data.refresh)


@router.get("/me", response=UserResponseDTO, auth=UnifiedJWTAuthentication())
async def get_current_user(request):
    return request.user


@router.post("/logout", auth=UnifiedJWTAuthentication())
async def logout(request):
    access_token_str = request.auth
    refresh_token_str = request.COOKIES.get(
        settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
    )

    await container.auth_service.logout(access_token_str, refresh_token_str)

    response = JsonResponse({"message": "Successfully logged out"})

    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
    response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])

    return response
