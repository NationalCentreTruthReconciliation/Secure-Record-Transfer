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
        context["accepted_files"] = settings.ACCEPTED_FILE_FORMATS
        context["max_total_upload_size"] = settings.MAX_TOTAL_UPLOAD_SIZE
        context["max_single_upload_size"] = settings.MAX_SINGLE_UPLOAD_SIZE
        context["max_total_upload_count"] = settings.MAX_TOTAL_UPLOAD_COUNT
        return context
