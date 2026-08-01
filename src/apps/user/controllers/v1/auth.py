from loguru import logger
from ninja import Router

from apps.common.utils.ratelimit import enforce_rate_limit
from apps.user.dto.schemas import (
    LoginRequestDTO,
    LoginResponseDTO,
    LogoutRequestDTO,
    RefreshRequestDTO,
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
    await enforce_rate_limit(request, scope="register", limit=10, window_seconds=3600)
    user = await container.user_service.create_user(data)
    try:
        # Background jobs must never break the request path they were
        # triggered from; a stalled worker/Redis just means the job is
        # skipped (and logged) instead of failing registration.
        await container.queue_service.enqueue(
            "log_event", f"New user registered: {user.phone}"
        )
    except Exception:
        logger.warning("Failed to enqueue log_event for {}", user.phone)
    return user


@router.post("/login", response=LoginResponseDTO)
async def login(
    request,
    data: LoginRequestDTO,
):
    await enforce_rate_limit(
        request, scope="login", limit=5, window_seconds=300, extra_key=data.phone
    )
    return await container.auth_service.login(data.phone, data.password)


@router.post("/refresh", response=RefreshResponseDTO)
async def refresh_token(
    request,
    data: RefreshRequestDTO,
):
    await enforce_rate_limit(request, scope="refresh", limit=20, window_seconds=300)
    return await container.auth_service.refresh_token(data.refresh)


@router.get("/me", response=UserResponseDTO, auth=UnifiedJWTAuthentication())
async def get_current_user(request):
    return request.user


@router.post("/logout", auth=UnifiedJWTAuthentication())
async def logout(
    request,
    data: LogoutRequestDTO = None,
):
    access_token_str = request.auth
    refresh_token_str = data.refresh if data else None

    await container.auth_service.logout(access_token_str, refresh_token_str)

    return {"message": "Successfully logged out"}
