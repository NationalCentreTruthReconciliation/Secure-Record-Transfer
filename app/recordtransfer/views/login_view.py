import logging

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class HTMXLoginView(LoginView):
    """Custom LoginView that supports HTMX requests for login forms."""

    template_name = "registration/login.html"

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        """Successful login handler."""
        super().form_valid(form)
        if self.request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response
        return redirect(self.get_success_url())

    def form_invalid(self, form: AuthenticationForm) -> HttpResponse:
        """Handle invalid login form submissions."""
        if self.request.headers.get("HX-Request"):
            html = render_to_string(
                "registration/login_errors.html",  # Changed to form-only template
                {"form": form},
                request=self.request,
            )
            return HttpResponse(html)
        return super().form_invalid(form)
