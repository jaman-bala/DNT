from asgiref.sync import sync_to_async
from django.contrib.auth import aauthenticate
from ninja.errors import HttpError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.user.dto.schemas import LoginResponseDTO, RefreshResponseDTO
from apps.user.services.blacklist_service import BlacklistService
from apps.user.utils.password import is_password_change_required
from config.base.base_service import BaseService


class AuthService(BaseService):
    def __init__(self, blacklist_service: BlacklistService):
        super().__init__()
        self.blacklist_service = blacklist_service

    async def login(self, phone: str, password: str) -> LoginResponseDTO:
        user = await aauthenticate(username=phone, password=password)
        if not user:
            raise HttpError(401, "Invalid credentials")

        if not user.is_active:
            raise HttpError(401, "User account is disabled")

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
