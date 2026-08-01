import logging

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
    Bearer-token JWT authentication. Works with Swagger UI and regular API calls.
    """

    async def authenticate(self, request: HttpRequest, token: str) -> str | None:
        user = await self._get_user_from_token(token)
        if user:
            request.user = user
            return token
        return None

    async def _get_user_from_token(self, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
            )

            # Reject refresh tokens (and anything else) presented as an access token.
            if payload.get("token_type") != "access":
                logger.warning("Token with wrong token_type used as access token")
                return None

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
