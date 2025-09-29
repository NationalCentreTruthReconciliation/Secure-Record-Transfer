from django.http import HttpRequest, HttpResponse
from django.views.i18n import JavaScriptCatalog
from utility import get_js_translation_version


class AppJavaScriptCatalog(JavaScriptCatalog):
    """Add JavaScript-Catalog-Version header to response to vary cache on."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Add JavaScript-Catalog-Version header to response."""
        response = super().get(request, *args, **kwargs)
        response["JavaScript-Catalog-Version"] = get_js_translation_version()
        return response
