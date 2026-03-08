import logging

import jwt
from apps.user.services.blacklist_service import BlacklistService
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)
User = get_user_model()


class UnifiedJWTAuthentication(HttpBearer):
    """
    Unified JWT authentication supporting both Bearer tokens and cookies.
    Works with Swagger UI and regular API calls.
    """

    def authenticate(self, request: HttpRequest, token: str = None) -> str | None:
        """
        Authenticate using Bearer token (for Swagger) or cookies (for regular requests).
        """
        # If token is provided (from Bearer auth), use it directly
        if token:
            user = self._get_user_from_token(token)
            if user:
                request.user = user
                return token
            return None

        # Otherwise, try to get token from cookies or Authorization header
        return self._authenticate_from_request(request)

    def _authenticate_from_request(self, request: HttpRequest) -> str | None:
        """Authenticate from Authorization header or cookies"""
        # 1. Проверяем заголовок Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user = self._get_user_from_token(token)
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
            user = self._get_user_from_token(access_token)
            if user:
                request.user = user
                return access_token
            logger.warning("Access token from cookie invalid")

        # 3. Если есть refresh_token, пробуем обновить
        if refresh_token:
            user, new_token = self._refresh_access_token(refresh_token)
            if user:
                request.user = user
                request.new_access_token = new_token  # можно использовать на фронте
                return new_token
            logger.error("Refresh token invalid")

        return None

    def _get_user_from_token(self, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
            )
            jti = payload.get("jti")
            if jti and BlacklistService.is_blacklisted(jti):
                logger.warning(f"Token {jti} is blacklisted")
                return None

            user_id = payload.get("user_id")
            if user_id:
                return User.objects.get(id=user_id)
            return None
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    def _refresh_access_token(
        self, refresh_token: str
    ) -> tuple[User | None, str | None]:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
            )
            jti = payload.get("jti")
            if jti and BlacklistService.is_blacklisted(jti):
                logger.warning(f"Refresh token {jti} is blacklisted")
                return None, None

            user_id = payload.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                new_access_token = jwt.encode(
                    {"user_id": str(user.id)},
                    settings.SIMPLE_JWT["SIGNING_KEY"],
                    algorithm=settings.SIMPLE_JWT["ALGORITHM"],
                )
                return user, new_access_token
            return None, None
        except Exception as e:
            logger.error(f"Refresh token failed: {e}")
            return None, None
