from django.conf import settings
from django.http import JsonResponse
from ninja import File, Form, Router
from ninja.files import UploadedFile

from apps.user.dto.schemas import (
    LoginRequestDTO,
    LoginResponseDTO,
    RefreshRequestDTO,
    RefreshResponseDTO,
    UserFormDataDTO,
    UserResponseDTO,
)
from config.auth.authentication import UnifiedJWTAuthentication
from config.container import container

router = Router(tags=["Authentication and Authorization"])


@router.post("/register", response=UserResponseDTO)
async def register_user(
    request,
    phone: str = Form(...),
    email: str | None = Form(None),
    password: str = Form(...),
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

    data = UserFormDataDTO(
        phone=phone,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
    )
    user = await container.user_service.create_user(
        data, profile_image_url=profile_image_url
    )
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
