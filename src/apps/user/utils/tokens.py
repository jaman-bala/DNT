import uuid
from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings

from apps.user.exceptions import InvalidTokenError

PASSWORD_RESET_TOKEN_LIFETIME = timedelta(minutes=30)
EMAIL_VERIFICATION_TOKEN_LIFETIME = timedelta(hours=24)


def generate_action_token(user, token_type: str, lifetime: timedelta) -> str:
    """
    Short-lived, single-use JWT for out-of-band actions (password reset,
    email verification). Signed with the same key/algorithm as access/refresh
    tokens but a distinct `token_type`, so UnifiedJWTAuthentication — which
    only ever accepts token_type == "access" — rejects these automatically.
    """
    now = datetime.now(UTC)
    payload = {
        "user_id": str(user.id),
        "token_type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        # int, not float: BlacklistService.add_to_blacklist expects an int
        # epoch (matching simplejwt's own exp claim convention) or a datetime.
        "exp": int((now + lifetime).timestamp()),
    }
    return jwt.encode(
        payload,
        settings.SIMPLE_JWT["SIGNING_KEY"],
        algorithm=settings.SIMPLE_JWT["ALGORITHM"],
    )


async def verify_action_token(
    token: str, expected_type: str, blacklist_service
) -> tuple[uuid.UUID, str, float]:
    """
    Decode and validate an action token, returning (user_id, jti, exp).
    Raises InvalidTokenError on any failure (bad signature, expired, wrong
    type, or already-used/blacklisted). The caller must blacklist the jti
    (using the returned exp as the blacklist TTL) after successfully
    consuming the token, to enforce single use.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SIMPLE_JWT["SIGNING_KEY"],
            algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
        )
    except Exception as e:
        raise InvalidTokenError() from e

    if payload.get("token_type") != expected_type:
        raise InvalidTokenError()

    jti = payload.get("jti")
    user_id = payload.get("user_id")
    exp = payload.get("exp")
    if not jti or not user_id or not exp:
        raise InvalidTokenError()

    if await blacklist_service.is_blacklisted(jti):
        raise InvalidTokenError()

    try:
        return uuid.UUID(user_id), jti, exp
    except ValueError as e:
        raise InvalidTokenError() from e
