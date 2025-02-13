"""Views for the homepage and static pages navigable from the home page."""

from django.conf import settings
from django.views.generic import TemplateView

from caais.models import RightsType, SourceRole, SourceType


class Index(TemplateView):
    """The homepage."""

    template_name = "recordtransfer/home.html"


class SystemErrorPage(TemplateView):
    """The page a user sees when there is some system error."""

    template_name = "recordtransfer/systemerror.html"


class About(TemplateView):
    """About the application."""

    template_name = "recordtransfer/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ACCEPTED_FILE_FORMATS"] = settings.ACCEPTED_FILE_FORMATS
        context["MAX_TOTAL_UPLOAD_SIZE_MB"] = settings.MAX_TOTAL_UPLOAD_SIZE_MB
        context["MAX_SINGLE_UPLOAD_SIZE_MB"] = settings.MAX_SINGLE_UPLOAD_SIZE_MB
        context["MAX_TOTAL_UPLOAD_COUNT"] = settings.MAX_TOTAL_UPLOAD_COUNT
        context["source_types"] = SourceType.objects.all().exclude(name="Other").order_by("name")
        context["source_roles"] = SourceRole.objects.all().exclude(name="Other").order_by("name")
        context["rights_types"] = RightsType.objects.all().exclude(name="Other").order_by("name")
        return context
