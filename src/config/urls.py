from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.api import api_v1

urlpatterns = []

if settings.DEBUG:
    # Django Control Room (dev-only, see config/conf/installed_apps.py). Must
    # come before path("admin/", admin.site.urls) below — admin's own
    # catch-all view matches anything under admin/ first and would otherwise
    # 404 these before the resolver ever reaches them.
    urlpatterns += [
        path("admin/dj-urls-panel/", include("dj_urls_panel.urls")),
        path("admin/dj-redis-panel/", include("dj_redis_panel.urls")),
        path("admin/dj-cache-panel/", include("dj_cache_panel.urls")),
        path("admin/dj-control-room/", include("dj_control_room.urls")),
    ]

urlpatterns += [
    path("admin/", admin.site.urls),
    path("api/v1/", api_v1.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
