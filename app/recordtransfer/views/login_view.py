from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.shortcuts import redirect

import logging

logger = logging.getLogger(__name__)


class HTMXLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        """Successful login handler"""
        super().form_valid(form)
        if self.request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get("HX-Request"):
            html = render_to_string(
                "registration/login_form.html",  # Changed to form-only template
                {"form": form},
                request=self.request,
            )
            return HttpResponse(html)
        return super().form_invalid(form)
