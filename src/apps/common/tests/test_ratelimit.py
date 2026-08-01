from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.common.utils.ratelimit import check_rate_limit


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class CheckRateLimitTestCase(TestCase):
    def setUp(self):
        cache.clear()

    async def test_allows_requests_within_limit(self):
        for _ in range(3):
            allowed = await check_rate_limit("test:key", limit=3, window_seconds=60)
            self.assertTrue(allowed)

    async def test_blocks_requests_over_limit(self):
        for _ in range(3):
            await check_rate_limit("test:key2", limit=3, window_seconds=60)

        allowed = await check_rate_limit("test:key2", limit=3, window_seconds=60)
        self.assertFalse(allowed)

    async def test_keys_are_independent(self):
        for _ in range(3):
            await check_rate_limit("test:key3", limit=3, window_seconds=60)

        # A different key must not be affected by key3's usage.
        allowed = await check_rate_limit("test:key4", limit=3, window_seconds=60)
        self.assertTrue(allowed)
