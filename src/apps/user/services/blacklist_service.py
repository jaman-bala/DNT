from datetime import UTC, datetime

from django.core.cache import cache


class BlacklistService:
    async def add_to_blacklist(self, jti: str, expires_at: datetime | int) -> None:
        """
        Add a JTI (JWT ID) to the blacklist.
        The key will expire automatically based on the token's expiration time.
        """
        if isinstance(expires_at, int):
            expires_at = datetime.fromtimestamp(expires_at, tz=UTC)

        now = datetime.now(UTC)
        ttl = int((expires_at - now).total_seconds())
        if ttl > 0:
            await cache.aset(f"blacklist:{jti}", "true", timeout=ttl)

    async def is_blacklisted(self, jti: str) -> bool:
        """
        Check if a JTI is in the blacklist.
        """
        return await cache.aget(f"blacklist:{jti}") is not None
