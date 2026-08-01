from django.core.cache import cache
from django.http import HttpRequest
from ninja.errors import HttpError


async def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """
    Fixed-window request counter backed by the Django cache (Redis).
    Returns True if the caller is still within `limit` for this window.
    """
    await cache.aadd(key, 0, timeout=window_seconds)
    count = await cache.aincr(key)
    return count <= limit


def _client_ip(request: HttpRequest) -> str:
    return request.META.get("REMOTE_ADDR", "unknown")


async def enforce_rate_limit(
    request: HttpRequest,
    *,
    scope: str,
    limit: int,
    window_seconds: int,
    extra_key: str | None = None,
) -> None:
    """
    Raise HTTP 429 if the caller exceeded `limit` requests for `scope` within
    `window_seconds`. Keyed by client IP + scope, optionally narrowed further
    by `extra_key` (e.g. the phone number being logged in) to also cap
    attempts per-account rather than just per-IP.
    """
    parts = [scope, _client_ip(request)]
    if extra_key:
        parts.append(extra_key)
    key = "ratelimit:" + ":".join(parts)

    if not await check_rate_limit(key, limit, window_seconds):
        raise HttpError(429, "Too many requests, try again later.")
