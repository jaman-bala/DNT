from django.templatetags.static import static
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Blog admin panel",
    "SITE_HEADER": "Blog admin panel",
    "SITE_SUBHEADER": "Blog admin panel",
    "SITE_URL": "https://president.kg/",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/jpeg",
            "href": "https://st4.depositphotos.com/4018617/31061/v/1600/depositphotos_310617096-stock-illustration-%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD.jpg",
        },
    ],
    "SHOW_BACK_BUTTON": True,
    "ENVIRONMENT": "config.conf.admin.environment_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Users",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:user_user_changelist"),
                    },
                ],
            },
        ],
    },
    "SCRIPTS": [
        lambda request: static("js/admin-row-clickable.js"),
    ],
    "LOGIN": {
        "image": lambda request: "https://foto.papik.pro/uploads/posts/2025-05/30/17486248253786.jpg",
    },
}


def environment_callback(request):
    """Callback to display the current environment in the admin panel."""
    from config.settings import DEBUG

    if DEBUG:
        return ["Development", "info"]
    return ["Production", "warning"]
