from config.conf.cache import REDIS_URL
from config.utils import env

# https://django-control-room.github.io/dj-control-room/configuration/
DJ_CONTROL_ROOM_SETTINGS = {
    # Matches the admin skin this template ships with (django-unfold).
    "EXTRA_CSS": ["dj_control_room_base/css/themes/unfold.css"],
    # AI agent integration (MCP). Off by default — turn on by setting all
    # three env vars below; MCP_USERNAME must be an existing staff user.
    "MCP_ENABLED": env("DJ_CONTROL_ROOM_MCP_ENABLED", default=False, is_bool=True),
    "MCP_TOKEN": env("DJ_CONTROL_ROOM_MCP_TOKEN", default=None),
    "MCP_USERNAME": env("DJ_CONTROL_ROOM_MCP_USERNAME", default=None),
}

# https://django-control-room.github.io/dj-urls-panel/configuration/
DJ_URLS_PANEL_SETTINGS: dict = {}

# https://django-control-room.github.io/dj-redis-panel/
DJ_REDIS_PANEL_SETTINGS = {
    # Safe read-mostly defaults for a shared dev instance also used by the
    # cache, rate limiter, and arq queue — don't let the panel delete keys.
    "ALLOW_KEY_DELETE": False,
    "ALLOW_KEY_EDIT": True,
    "ALLOW_TTL_UPDATE": True,
    "INSTANCES": {
        "default": {
            "description": "DNT Redis (cache / rate limiting / arq)",
            "url": REDIS_URL,
        },
    },
}

# https://django-control-room.github.io/dj-cache-panel/ — reads settings.CACHES
# directly, no INSTANCES to declare. Same reasoning as DJ_REDIS_PANEL_SETTINGS
# above: this is the same shared Redis behind rate limiting/blacklist, so lock
# down delete/flush on it rather than leaving the backend's full ability set on.
DJ_CACHE_PANEL_SETTINGS = {
    "CACHES": {
        "default": {
            "abilities": {
                "delete_key": False,
                "flush_cache": False,
            },
        },
    },
}
