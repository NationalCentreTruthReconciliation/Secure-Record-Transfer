"""Views for creating and activating user accounts."""

from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import FormView, TemplateView

from recordtransfer.emails import send_user_activation_email
from recordtransfer.forms import SignUpForm
from recordtransfer.models import User
from recordtransfer.tokens import account_activation_token


class CreateAccount(FormView):
    """Allows a user to create a new account with the SignUpForm. When the form is submitted
    successfully, send an email to that user with a link that lets them activate their account.
    """

    template_name = "recordtransfer/signupform.html"
    form_class = SignUpForm
    success_url = reverse_lazy("recordtransfer:activation_sent")

    def form_valid(self, form):
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.gets_submission_email_updates = False
        new_user.save()
        send_user_activation_email.delay(new_user)
        return super().form_valid(form)


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.confirmed_email = True
        user.save()
        login(request, user)
        return HttpResponseRedirect(reverse("recordtransfer:account_created"))

    return HttpResponseRedirect(reverse("recordtransfer:activation_invalid"))


class ActivationSent(TemplateView):
    """The page a user sees after creating an account."""

    template_name = "recordtransfer/activation_sent.html"


class ActivationComplete(TemplateView):
    """The page a user sees when their account has been activated."""

    template_name = "recordtransfer/activation_complete.html"


class ActivationInvalid(TemplateView):
    """The page a user sees if their account could not be activated."""

    template_name = "recordtransfer/activation_invalid.html"
