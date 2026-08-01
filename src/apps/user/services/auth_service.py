import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import aauthenticate
from django.utils import timezone
from ninja.errors import HttpError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.common.services.queue_service import QueueService
from apps.user.dto.schemas import LoginResponseDTO, RefreshResponseDTO
from apps.user.exceptions import InvalidPasswordError, InvalidTokenError
from apps.user.models.users import User
from apps.user.services.blacklist_service import BlacklistService
from apps.user.utils.password import is_password_change_required
from apps.user.utils.tokens import (
    PASSWORD_RESET_TOKEN_LIFETIME,
    generate_action_token,
    verify_action_token,
)
from config.base.base_service import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    def __init__(
        self, blacklist_service: BlacklistService, queue_service: QueueService
    ):
        super().__init__()
        self.blacklist_service = blacklist_service
        self.queue_service = queue_service

    async def login(self, phone: str, password: str) -> LoginResponseDTO:
        user = await aauthenticate(username=phone, password=password)
        if not user:
            raise HttpError(401, "Invalid credentials")

        if not user.is_active:
            raise HttpError(401, "User account is disabled")

        if (
            settings.REQUIRE_EMAIL_VERIFICATION
            and user.email
            and not user.email_verified
        ):
            raise HttpError(403, "Email not verified")

        # RefreshToken is synchronous and might hit the DB, so we wrap it
        @sync_to_async
        def get_tokens(user_obj):
            refresh = RefreshToken.for_user(user_obj)
            refresh["user_id"] = str(user_obj.id)
            return str(refresh.access_token), str(refresh)

        access_token_str, refresh_token_str = await get_tokens(user)

        # is_password_change_required doesn't hit DB if data is loaded, but just in case
        password_change_required = is_password_change_required(user)

        return LoginResponseDTO(
            access=access_token_str,
            refresh=refresh_token_str,
            password_change_required=password_change_required,
        )

    async def refresh_token(self, refresh_token_str: str) -> RefreshResponseDTO:
        try:

            @sync_to_async
            def generate_new_access(token_str):
                refresh_token = RefreshToken(token_str)
                # Ensure user_id is properly formatted string
                refresh_token["user_id"] = str(refresh_token.payload.get("user_id"))
                return str(refresh_token.access_token)

            new_access_token = await generate_new_access(refresh_token_str)
            return RefreshResponseDTO(access=new_access_token)
        except Exception as e:
            raise HttpError(401, f"Invalid refresh token: {str(e)}") from e

    async def logout(
        self, access_token_str: str | None, refresh_token_str: str | None
    ) -> None:
        if access_token_str:
            try:

                @sync_to_async
                def get_access_payload(token_str):
                    token = AccessToken(token_str)
                    return token["jti"], token.payload["exp"]

                jti, exp = await get_access_payload(access_token_str)
                await self.blacklist_service.add_to_blacklist(jti, exp)
            except Exception:
                pass

        if refresh_token_str:
            try:

                @sync_to_async
                def get_refresh_payload(token_str):
                    token = RefreshToken(token_str)
                    return token["jti"], token.payload["exp"]

                jti, exp = await get_refresh_payload(refresh_token_str)
                await self.blacklist_service.add_to_blacklist(jti, exp)
            except Exception:
                pass

    async def request_password_reset(self, email: str) -> None:
        """
        Enqueue a password-reset email if `email` matches an account. Always
        succeeds from the caller's point of view (no account enumeration) —
        an unknown email simply results in no email being sent.
        """
        try:
            user = await User.objects.aget(email=email)
        except User.DoesNotExist:
            return

        token = generate_action_token(
            user, "password_reset", PASSWORD_RESET_TOKEN_LIFETIME
        )
        try:
            await self.queue_service.enqueue(
                "send_password_reset_email", str(user.id), token
            )
        except Exception:
            logger.warning("Failed to enqueue password reset email for %s", email)

    async def confirm_password_reset(
        self, token: str, new_password: str, confirm_password: str
    ) -> None:
        """Verify a password-reset token and set the new password."""
        if new_password != confirm_password:
            raise InvalidPasswordError("New passwords do not match")

        user_id, jti, exp = await verify_action_token(
            token, "password_reset", self.blacklist_service
        )
        try:
            user = await User.objects.aget(id=user_id)
        except User.DoesNotExist:
            raise InvalidTokenError() from None

        await sync_to_async(user.set_password)(new_password)
        user.password_changed_at = timezone.now()
        await user.asave()

        # Single-use: blacklist immediately so the same link can't be replayed.
        await self.blacklist_service.add_to_blacklist(jti, exp)
