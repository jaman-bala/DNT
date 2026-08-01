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
from asgiref.sync import sync_to_async  # noqa: E402
from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.mail import send_mail  # noqa: E402
from django.template.loader import render_to_string  # noqa: E402
from loguru import logger  # noqa: E402

User = get_user_model()


async def log_event(ctx: dict, message: str) -> None:
    """Demo task — replace with real jobs (emails, image processing, etc.)."""
    logger.info("[arq] {}", message)


async def send_password_reset_email(ctx: dict, user_id: str, token: str) -> None:
    try:
        user = await User.objects.aget(id=user_id)
    except User.DoesNotExist:
        return

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    body = await sync_to_async(render_to_string)(
        "email/password_reset.txt", {"user": user, "reset_url": reset_url}
    )
    await sync_to_async(send_mail)(
        subject="Сброс пароля",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


async def send_verification_email(ctx: dict, user_id: str, token: str) -> None:
    try:
        user = await User.objects.aget(id=user_id)
    except User.DoesNotExist:
        return

    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    body = await sync_to_async(render_to_string)(
        "email/verify_email.txt", {"user": user, "verify_url": verify_url}
    )
    await sync_to_async(send_mail)(
        subject="Подтверждение email",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


class WorkerSettings:
    functions = [log_event, send_password_reset_email, send_verification_email]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
