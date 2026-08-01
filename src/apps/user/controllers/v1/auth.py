from loguru import logger
from ninja import Router

from apps.common.utils.ratelimit import enforce_rate_limit
from apps.user.dto.schemas import (
    EmailVerificationConfirmDTO,
    LoginRequestDTO,
    LoginResponseDTO,
    LogoutRequestDTO,
    MessageResponseDTO,
    PasswordResetConfirmDTO,
    PasswordResetRequestDTO,
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

    if user.email:
        # request_email_verification already logs and swallows enqueue failures.
        await container.user_service.request_email_verification(user)

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


@router.post("/password-reset/request", response=MessageResponseDTO)
async def request_password_reset(
    request,
    data: PasswordResetRequestDTO,
):
    await enforce_rate_limit(
        request,
        scope="password-reset-request",
        limit=5,
        window_seconds=3600,
        extra_key=data.email,
    )
    await container.auth_service.request_password_reset(data.email)
    return {
        "message": "If an account with that email exists, a reset link has been sent."
    }


@router.post("/password-reset/confirm", response=MessageResponseDTO)
async def confirm_password_reset(
    request,
    data: PasswordResetConfirmDTO,
):
    await enforce_rate_limit(
        request, scope="password-reset-confirm", limit=10, window_seconds=3600
    )
    await container.auth_service.confirm_password_reset(
        data.token, data.new_password, data.confirm_password
    )
    return {"message": "Password has been reset successfully."}


@router.post(
    "/email/verify/resend",
    response=MessageResponseDTO,
    auth=UnifiedJWTAuthentication(),
)
async def resend_email_verification(request):
    await enforce_rate_limit(
        request,
        scope="email-verify-resend",
        limit=5,
        window_seconds=3600,
        extra_key=str(request.user.id),
    )
    await container.user_service.request_email_verification(request.user)
    return {"message": "Verification email sent."}


@router.post("/email/verify/confirm", response=MessageResponseDTO)
async def confirm_email_verification(
    request,
    data: EmailVerificationConfirmDTO,
):
    await enforce_rate_limit(
        request, scope="email-verify-confirm", limit=10, window_seconds=3600
    )
    await container.user_service.confirm_email_verification(data.token)
    return {"message": "Email verified successfully."}
