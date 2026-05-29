from django.urls import reverse_lazy
from django.templatetags.static import static

UNFOLD = {
    "SITE_TITLE": "DNT admin panel",
    "SITE_HEADER": "",
    "SITE_SUBHEADER": "",
    "SITE_LOGO": {
        "light": lambda request: static("img/logo_light.svg"),
        "dark": lambda request: static("img/logo_dark.svg"),
    },
    "SITE_URL": "https://github.com/jaman-bala/DNT",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("img/favicon.svg"),
        },
    ],  # логотип в фавиконках
    "SHOW_BACK_BUTTON": True,
    "ENVIRONMENT": "config.conf.admin.environment_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Управление пользователями",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Пользователи",
                        "icon": "group",
                        "link": reverse_lazy("admin:user_user_changelist"),
                    },
                ],
            },
        ],
    },
    "LOGIN": {
        "image": lambda request: (
            "http://foto.papik.pro/uploads/posts/2025-05/30/17486248253786.jpg"
        ),
    },
}


def environment_callback(request):
    """Callback to display the current environment in the admin panel."""
    from config.settings import DEBUG

    if DEBUG:
        return ["Development", "info"]
    return ["Production", "warning"]
