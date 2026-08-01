"""
arq worker entrypoint. Run with:

    uv run arq apps.common.worker.WorkerSettings

Add your own background jobs as async functions and list them in
`WorkerSettings.functions`. Enqueue them from anywhere via
`container.queue_service.enqueue("job_name", *args, **kwargs)`.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from arq.connections import RedisSettings  # noqa: E402
from django.conf import settings  # noqa: E402
from loguru import logger  # noqa: E402


async def log_event(ctx: dict, message: str) -> None:
    """Demo task — replace with real jobs (emails, image processing, etc.)."""
    logger.info("[arq] {}", message)


class WorkerSettings:
    functions = [log_event]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
