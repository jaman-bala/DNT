from pathlib import Path

from dotenv import load_dotenv
from split_settings.tools import include

from .utils import env

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env("DEBUG", default=False, is_bool=True)
# ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
ALLOWED_HOSTS = ["*"]

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
    "conf/admin.py",
)
