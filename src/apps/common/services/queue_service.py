import asyncio
from typing import Any

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from django.conf import settings


class QueueService:
    """
    Thin wrapper around an arq connection pool for enqueueing background jobs.
    The pool is created lazily (arq's create_pool is a coroutine, so it can't
    be built eagerly in __init__) and cached, mirroring S3Service's lazy
    client property.
    """

    def __init__(self):
        self._pool: ArqRedis | None = None
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> ArqRedis:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await create_pool(
                        RedisSettings.from_dsn(settings.REDIS_URL)
                    )
        return self._pool

    async def enqueue(self, job_name: str, *args: Any, **kwargs: Any) -> None:
        """Enqueue a job by name for the arq worker (see apps/common/worker.py)."""
        pool = await self._get_pool()
        await pool.enqueue_job(job_name, *args, **kwargs)
