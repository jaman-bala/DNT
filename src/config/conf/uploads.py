from config.utils import env

# Per-file cap enforced by the /common/upload endpoint. The much larger
# DATA_UPLOAD_MAX_MEMORY_SIZE in settings.py is only the Django-wide hard
# ceiling, not a sane per-file limit.
MAX_UPLOAD_SIZE = int(env("MAX_UPLOAD_SIZE", default=10 * 1024 * 1024))  # 10 MB

# Extensions accepted by the generic upload endpoint. Extend this list (and
# EXTENSION_CONTENT_TYPES in apps/common/controllers/v1/upload.py) when your
# own models need to accept other file types.
ALLOWED_UPLOAD_EXTENSIONS = env.list(
    "ALLOWED_UPLOAD_EXTENSIONS", default=["jpg", "jpeg", "png", "webp"]
)
