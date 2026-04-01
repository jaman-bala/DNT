import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja.security import HttpBearer

from config.container import container

logger = logging.getLogger(__name__)
User = get_user_model()


class UnifiedJWTAuthentication(HttpBearer):
    """
    Unified JWT authentication supporting both Bearer tokens and cookies.
    Works with Swagger UI and regular API calls.
    """

    async def authenticate(self, request: HttpRequest, token: str = None) -> str | None:
        """
        Authenticate using Bearer token (for Swagger) or cookies (for regular requests).
        """
        # If token is provided (from Bearer auth), use it directly
        if token:
            user = await self._get_user_from_token(token)
            if user:
                request.user = user
                return token
            return None

        # Otherwise, try to get token from cookies or Authorization header
        return await self._authenticate_from_request(request)

    async def _authenticate_from_request(self, request: HttpRequest) -> str | None:
        """Authenticate from Authorization header or cookies"""
        # 1. Проверяем заголовок Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user = await self._get_user_from_token(token)
            if user:
                request.user = user
                return token
            logger.warning("Header token invalid")

        # 2. Проверяем cookies
        access_token = request.COOKIES.get(
            settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token")
        )
        refresh_token = request.COOKIES.get(
            settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
        )

        if access_token:
            user = await self._get_user_from_token(access_token)
            if user:
                request.user = user
                return access_token
            logger.warning("Access token from cookie invalid")

        # 3. Если есть refresh_token, пробуем обновить
        if refresh_token:
            user, new_token = await self._refresh_access_token(refresh_token)
            if user:
                request.user = user
                request.new_access_token = new_token  # можно использовать на фронте
                return new_token
            logger.error("Refresh token invalid")

        return None

    async def _get_user_from_token(self, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
            )
            jti = payload.get("jti")
            if jti and await container.blacklist_service.is_blacklisted(jti):
                logger.warning("Token %s is blacklisted", jti)
                return None

            user_id = payload.get("user_id")
            if user_id:
                return await User.objects.aget(id=user_id)
            return None
        except Exception as e:
            logger.warning("Token validation failed: %s", e)
            return None

    async def _refresh_access_token(
        self, refresh_token: str
    ) -> tuple[User | None, str | None]:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
            )
            jti = payload.get("jti")
            if jti and await container.blacklist_service.is_blacklisted(jti):
                logger.warning("Refresh token %s is blacklisted", jti)
                return None, None

            user_id = payload.get("user_id")
            if user_id:
                user = await User.objects.aget(id=user_id)
                exp = datetime.now(UTC) + settings.SIMPLE_JWT.get(
                    "ACCESS_TOKEN_LIFETIME", timedelta(minutes=5)
                )
                new_access_token = jwt.encode(
                    {
                        "user_id": str(user.id),
                        "exp": exp.timestamp(),
                        "jti": uuid.uuid4().hex,
                        "token_type": "access",
                    },
                    settings.SIMPLE_JWT["SIGNING_KEY"],
                    algorithm=settings.SIMPLE_JWT["ALGORITHM"],
                )
                return user, new_access_token
            return None, None
        except Exception as e:
            logger.error("Refresh token failed: %s", e)
            return None, None
