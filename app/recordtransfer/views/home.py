"""Views for the homepage and static pages navigable from the home page."""

from django.conf import settings
from django.views.generic import TemplateView


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
        return context
