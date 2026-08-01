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
