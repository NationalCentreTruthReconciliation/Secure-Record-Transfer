"""Views for the homepage and static pages navigable from the home page."""

from typing import Any

from caais.models import RightsType, SourceRole, SourceType
from django.conf import settings
from django.views.generic import TemplateView


class Index(TemplateView):
    """The homepage."""

    template_name = "recordtransfer/home.html"


class Help(TemplateView):
    """The help page."""

    template_name = "recordtransfer/help.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add context variables to the template context."""
        context = super().get_context_data(**kwargs)
        context["source_types"] = SourceType.objects.all().exclude(name="Other").order_by("name")
        context["source_roles"] = SourceRole.objects.all().exclude(name="Other").order_by("name")
        context["rights_types"] = RightsType.objects.all().exclude(name="Other").order_by("name")

        context["MAX_TOTAL_UPLOAD_SIZE_MB"] = settings.MAX_TOTAL_UPLOAD_SIZE_MB
        context["MAX_TOTAL_UPLOAD_COUNT"] = settings.MAX_TOTAL_UPLOAD_COUNT

        return context


class About(TemplateView):
    """About the application."""

    template_name = "recordtransfer/about.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add context variables to the template context."""
        context = super().get_context_data(**kwargs)
        context["ACCEPTED_FILE_FORMATS"] = settings.ACCEPTED_FILE_FORMATS
        context["MAX_TOTAL_UPLOAD_SIZE_MB"] = settings.MAX_TOTAL_UPLOAD_SIZE_MB
        context["MAX_SINGLE_UPLOAD_SIZE_MB"] = settings.MAX_SINGLE_UPLOAD_SIZE_MB
        context["MAX_TOTAL_UPLOAD_COUNT"] = settings.MAX_TOTAL_UPLOAD_COUNT

        return context
