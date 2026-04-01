from pathlib import Path

from dotenv import load_dotenv
from split_settings.tools import include

from .utils import env, read_secret, strtobool

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = read_secret("SECRET_KEY") or env(
    "SECRET_KEY", default="django-insecure-change-me-in-production"
)

_debug_secret = read_secret("DEBUG")
DEBUG = (
    strtobool(_debug_secret)
    if _debug_secret is not None
    else env("DEBUG", default=False, is_bool=True)
)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500 * 1024 * 1024

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "user.User"

include(
    "conf/installed_apps.py",
    "conf/cors.py",
    "conf/middleware.py",
    "conf/db.py",
    "conf/auth.py",
    "conf/jwt.py",
    "conf/i18n.py",
    "conf/storage_aws.py",
    "conf/templates.py",
    "conf/cache.py",
    "conf/admin.py",
)
