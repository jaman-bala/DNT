from config.utils import env

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = int(env("EMAIL_PORT", default=587))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True, is_bool=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# Base URL of the frontend app that hosts the reset-password / verify-email
# pages linked to from emails (this API never renders those pages itself).
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# If True, AuthService.login rejects users who have an email on file that
# isn't verified yet. Off by default so the template works out of the box
# without forcing an email step.
REQUIRE_EMAIL_VERIFICATION = env(
    "REQUIRE_EMAIL_VERIFICATION", default=False, is_bool=True
)
