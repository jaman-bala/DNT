from config.settings import DEBUG

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework_simplejwt",
]

MY_APPS = [
    "apps.user",
    "apps.note",
]

INSTALLED_APPS = [
    # Django
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
    "unfold.contrib.inlines",  # optional, if special inlines are needed
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    *THIRD_PARTY_APPS,
    *MY_APPS,
]

if DEBUG:
    INSTALLED_APPS += [
        "django_extensions",
        "debug_toolbar",
        # Django Control Room — admin-integrated introspection panels (URLs,
        # Redis, Celery, ...) plus an optional MCP endpoint for AI agents.
        # Dev-only by design: see config/conf/control_room.py.
        "dj_control_room_base",
        "dj_urls_panel",
        "dj_control_room",
    ]
