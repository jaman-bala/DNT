from typing import Any

from django.http import HttpRequest, HttpResponse
from ninja.openapi.docs import DocsBase


class Scalar(DocsBase):
    """
    Renders API docs with Scalar (https://scalar.com) instead of Swagger UI.
    Scalar's UI is just a single script tag pointing at the OpenAPI JSON URL
    ninja already serves, loaded from the CDN — no extra pip dependency.
    """

    def render_page(
        self, request: HttpRequest, api: Any, **kwargs: Any
    ) -> HttpResponse:
        openapi_json_url = self.get_openapi_url(api, kwargs)
        return HttpResponse(f"""<!doctype html>
<html>
  <head>
    <title>{api.title} — API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script id="api-reference" data-url="{openapi_json_url}"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>""")
