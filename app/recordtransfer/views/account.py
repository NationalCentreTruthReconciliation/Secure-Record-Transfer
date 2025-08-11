"""Views for creating and activating user accounts."""

import logging
from typing import cast

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, PasswordResetView
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import get_language, gettext, ngettext
from django.views import View
from django.views.generic import FormView, TemplateView
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event

from recordtransfer.emails import send_user_activation_email
from recordtransfer.forms import SignUpForm
from recordtransfer.forms.user_forms import AsyncPasswordResetForm
from recordtransfer.models import User
from recordtransfer.tokens import account_activation_token

LOGGER = logging.getLogger(__name__)


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
        new_user.language = getattr(self.request, "LANGUAGE_CODE", get_language())
        new_user.save()
        send_user_activation_email.delay(new_user)
        if self.request.htmx:
            return HttpResponseClientRedirect(self.get_success_url())

        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid signup form submissions."""
        if self.request.htmx:
            # Return only the error template for HTMX requests
            html = render_to_string(
                "recordtransfer/signup_form.html",
                {"form": form},
                request=self.request,
            )
            return HttpResponse(html)
        return super().form_invalid(form)


def _set_language_cookie(response: HttpResponse, lang_code: str) -> HttpResponse:
    """Set the language cookie on the response based on user's preference."""
    response.set_cookie(
        key=settings.LANGUAGE_COOKIE_NAME,
        value=lang_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


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
                login(request, user, backend="axes.backends.AxesBackend")
                return _set_language_cookie(
                    redirect("recordtransfer:account_created"), user.language
                )
            else:
                return redirect("recordtransfer:activation_invalid")

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            LOGGER.exception("Unexpected error during account activation")
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


class Login(LoginView):
    """Custom LoginView that supports HTMX requests for login forms."""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        """Handle successful login."""
        response = super().form_valid(form)
        user = cast(User, form.get_user())

        if self.request.htmx:
            htmx_response = HttpResponseClientRedirect(self.get_success_url())
            return _set_language_cookie(htmx_response, user.language)
        return _set_language_cookie(response, user.language)

    def form_invalid(self, form: AuthenticationForm) -> HttpResponse:
        """Handle invalid login form submissions."""
        if not self.request.htmx:
            return super().form_invalid(form)

        response = HttpResponse(
            render_to_string(
                "registration/login_errors.html",  # Changed to form-only template
                {"form": form},
                request=self.request,
            )
        )

        # While the user is locked out, number of failures is not included in the request
        failures = getattr(self.request, "axes_failures_since_start", None)
        if (
            failures is not None
            and settings.AXES_WARNING_THRESHOLD <= failures < settings.AXES_FAILURE_LIMIT
        ):
            num_tries_left = settings.AXES_FAILURE_LIMIT - failures
            response = trigger_client_event(
                response,
                "showWarning",
                {
                    "value": ngettext(
                        "You have %(count)s login attempt left before your account is locked out.",
                        "You have %(count)s login attempts left before your account is locked out.",
                        num_tries_left,
                    )
                    % {
                        "count": num_tries_left,
                    }
                },
            )

        return response


def lockout(request: HttpRequest, credentials: dict, *args, **kwargs) -> HttpResponse:
    """Handle lockout due to too many failed login attempts."""
    response = HttpResponse(status=429)
    return trigger_client_event(
        response,
        "showError",
        {
            "value": gettext(
                "You have been locked out due to too many failed login attempts. "
                "Please try again later."
            ),
        },
    )


class AsyncPasswordResetView(PasswordResetView):
    """The page a user sees when they request a password reset."""

    email_template_name = "registration/password_reset_email.txt"
    html_email_template_name = "registration/password_reset_email.html"
    form_class = AsyncPasswordResetForm
