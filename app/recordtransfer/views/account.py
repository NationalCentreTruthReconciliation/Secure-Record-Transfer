"""Views for creating and activating user accounts."""

from django.contrib.auth import login
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import FormView, TemplateView

from recordtransfer.emails import send_user_activation_email
from recordtransfer.forms import SignUpForm
from recordtransfer.models import User
from recordtransfer.tokens import account_activation_token


class CreateAccount(FormView):
    """Allows a user to create a new account with the SignUpForm. When the form is submitted
    successfully, send an email to that user with a link that lets them activate their account.
    """

    template_name = "recordtransfer/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("recordtransfer:activation_sent")

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """If the user is already authenticated, redirect them to the homepage."""
        if request.user.is_authenticated:
            return redirect("recordtransfer:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Save the new user and send them an activation email."""
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.gets_submission_email_updates = False
        new_user.save()
        send_user_activation_email.delay(new_user)
        if self.request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response

        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid signup form submissions."""
        if self.request.headers.get("HX-Request"):
            # Return only the error template for HTMX requests
            html = render_to_string(
                "recordtransfer/signup_form.html",
                {"form": form},
                request=self.request,
            )
            return HttpResponse(html)
        return super().form_invalid(form)


class ActivateAccount(View):
    """View for activating user accounts via email link."""

    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        """Handle GET request for account activation."""
        # Redirect authenticated users to homepage
        if request.user.is_authenticated:
            return redirect("recordtransfer:index")

        try:
            # Decode the user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            # Validate the token
            if account_activation_token.check_token(user, token) and not user.is_active:
                # Activate the user
                user.is_active = True
                user.save()
                login(request, user)
                return redirect("recordtransfer:account_created")
            else:
                return redirect("recordtransfer:activation_invalid")

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return redirect("recordtransfer:activation_invalid")


class ActivationSent(TemplateView):
    """The page a user sees after creating an account."""

    template_name = "recordtransfer/activation_sent.html"


class ActivationComplete(TemplateView):
    """The page a user sees when their account has been activated."""

    template_name = "recordtransfer/activation_complete.html"


class ActivationInvalid(TemplateView):
    """The page a user sees if their account could not be activated."""

    template_name = "recordtransfer/activation_invalid.html"
