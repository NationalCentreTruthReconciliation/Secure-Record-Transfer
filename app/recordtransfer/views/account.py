"""Views for creating and activating user accounts."""

import logging
from typing import cast

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth.views import LoginView, PasswordResetView
from django.dispatch import receiver
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
from recordtransfer.forms import SignUpForm, SignUpFormRecaptcha
from recordtransfer.forms.user_forms import AsyncPasswordResetForm
from recordtransfer.models import User
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import is_deployed_environment

LOGGER = logging.getLogger(__name__)


class CreateAccount(FormView):
    """Allows a user to create a new account with the SignUpForm. When the form is submitted
    successfully, send an email to that user with a link that lets them activate their account.
    """

    template_name = "recordtransfer/signup.html"
    success_url = reverse_lazy("recordtransfer:activation_sent")

    def get_form_class(self) -> type[BaseModelForm]:
        """Return the appropriate form class based on environment."""
        if is_deployed_environment():
            return SignUpFormRecaptcha
        return SignUpForm

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Redirect authenticated users to homepage."""
        if request.user.is_authenticated:
            # Log redirect of already authenticated user
            LOGGER.info(
                "Authenticated user redirected from login: username='%s', user_id=%s, ip=%s",
                request.user.username,
                request.user.pk,
                _get_client_ip(request),
            )
            return redirect("recordtransfer:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Save the new user and send them an activation email."""
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.gets_submission_email_updates = False
        new_user.language = getattr(self.request, "LANGUAGE_CODE", get_language())
        new_user.save()

        # Log successful account creation
        LOGGER.info(
            "New user account created: username='%s', email='%s', user_id=%s",
            new_user.username,
            new_user.email,
            new_user.pk,
        )

        send_user_activation_email.delay(new_user)

        # Log activation email sent
        LOGGER.info(
            "Activation email sent to user: username='%s', email='%s', user_id=%s",
            new_user.username,
            new_user.email,
            new_user.pk,
        )

        if self.request.htmx:
            return HttpResponseClientRedirect(self.get_success_url())

        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        """Handle invalid signup form submissions."""
        LOGGER.info(
            "Signup form invalid: errors=%s, ip=%s",
            form.errors.as_json(),
            self.request.META.get("REMOTE_ADDR"),
        )
        if self.request.htmx:
            # Return only the error template for HTMX requests
            html = render_to_string(
                "recordtransfer/signup_form.html",
                {"form": form},
                request=self.request,
            )
            return HttpResponse(html)
        return super().form_invalid(form)


def _get_client_ip(request: HttpRequest) -> str:
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip


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
            # Log redirect of already authenticated user
            LOGGER.info(
                "Authenticated user redirected from account activation: username='%s', user_id=%s, ip=%s",
                request.user.username,
                request.user.pk,
                _get_client_ip(request),
            )
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

                # Log successful account activation
                LOGGER.info(
                    "User account activated successfully: username='%s', email='%s', user_id=%s",
                    user.username,
                    user.email,
                    user.pk,
                )

                login(request, user, backend="axes.backends.AxesBackend")

                # Log successful login after activation
                LOGGER.info(
                    "User logged in after account activation: username='%s', user_id=%s, ip=%s",
                    user.username,
                    user.pk,
                    _get_client_ip(request),
                )

                return _set_language_cookie(
                    redirect("recordtransfer:account_created"), user.language
                )
            else:
                # Log failed activation attempt
                LOGGER.warning(
                    "Failed account activation attempt: username='%s', user_id=%s, reason='invalid_token_or_already_active'",
                    user.username,
                    user.pk,
                )
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

        # Log successful login
        LOGGER.info(
            "User logged in successfully: username='%s', user_id=%s, ip=%s",
            user.username,
            user.pk,
            _get_client_ip(self.request),
        )

        if self.request.htmx:
            htmx_response = HttpResponseClientRedirect(self.get_success_url())
            return _set_language_cookie(htmx_response, user.language)
        return _set_language_cookie(response, user.language)

    def form_invalid(self, form: AuthenticationForm) -> HttpResponse:
        """Handle invalid login form submissions."""
        # Log failed login attempt
        username = form.cleaned_data.get("username", "unknown") if form.cleaned_data else "unknown"
        LOGGER.warning(
            "Failed login attempt: username='%s', ip=%s",
            username,
            _get_client_ip(self.request),
        )

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


@receiver(user_logged_out)
def log_user_logout(sender: User, request: HttpRequest, user: User, **kwargs) -> None:
    """Log when a user logs out."""
    if user and request:
        LOGGER.info(
            "User logged out: username='%s', user_id=%s, ip=%s",
            user.username,
            user.pk,
            _get_client_ip(request),
        )
    elif request:
        LOGGER.info("Anonymous user logged out: ip=%s", _get_client_ip(request))


def lockout(request: HttpRequest, credentials: dict, *args, **kwargs) -> HttpResponse:
    """Handle lockout due to too many failed login attempts."""
    # Log account lockout
    username = credentials.get("username", "unknown")
    ip_address = _get_client_ip(request)
    LOGGER.warning(
        "Account locked out due to too many failed login attempts: username='%s', ip=%s",
        username,
        ip_address,
    )

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
