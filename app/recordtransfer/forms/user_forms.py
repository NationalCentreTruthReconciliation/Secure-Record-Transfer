import re
from typing import Any, ClassVar, Optional

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from recordtransfer.constants import HtmlIds
from recordtransfer.emails import send_password_reset_email
from recordtransfer.forms.mixins import ContactInfoFormMixin, VisibleCaptchaMixin
from recordtransfer.models import User


class SignUpForm(UserCreationForm):
    """Form for a user to create a new account."""

    class Meta:
        """Meta class for SignUpForm."""

        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def clean(self) -> dict[str, Any]:
        """Clean data, make sure username and email are not already in use."""
        # Check for duplicate username is handled by superclass UserCreationForm
        cleaned_data = super().clean()
        new_email = cleaned_data.get("email")
        if new_email and User.objects.filter(email__iexact=new_email).exists():
            self.add_error("email", f"The email {new_email} is already in use")
        return cleaned_data

    email = forms.EmailField(
        max_length=256, required=True, widget=forms.TextInput(), label=gettext("Email")
    )

    username = forms.CharField(
        max_length=256,
        min_length=6,
        required=True,
        widget=forms.TextInput(),
        label=gettext("Username"),
        help_text=gettext("This is the username you will use to log in to your account"),
    )

    first_name = forms.CharField(
        max_length=256,
        min_length=2,
        required=True,
        widget=forms.TextInput(),
        label=gettext("First name"),
    )

    last_name = forms.CharField(
        max_length=256,
        min_length=2,
        required=True,
        widget=forms.TextInput(),
        label=gettext("Last name"),
    )


class SignUpFormRecaptcha(SignUpForm, VisibleCaptchaMixin):
    """Form for a user to create a new account with reCAPTCHA."""


class UserAccountInfoForm(forms.ModelForm):
    """Form for updating a user's account information."""

    NAME_PATTERN = re.compile(
        r"""^[a-zA-Z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u01FF]+([ \-']{0,1}[a-zA-Z\u00C0-\u00D6
    \u00D8-\u00F6\u00F8-\u01FF]+){0,2}[.]{0,1}$"""
    )
    NAME_VALIDATION_MESSAGE = _(
        "Name must contain only letters and may include these symbols: ' - . \n"
    )

    first_name = forms.RegexField(
        regex=NAME_PATTERN,
        widget=forms.TextInput(attrs={"id": HtmlIds.ID_FIRST_NAME}),
        label=_("First Name"),
        required=False,
        error_messages={
            "invalid": _(NAME_VALIDATION_MESSAGE),
        },
    )
    last_name = forms.RegexField(
        regex=NAME_PATTERN,
        widget=forms.TextInput(attrs={"id": HtmlIds.ID_LAST_NAME}),
        label=_("Last Name"),
        required=False,
        error_messages={
            "invalid": _(NAME_VALIDATION_MESSAGE),
        },
    )
    gets_notification_emails = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"id": HtmlIds.ID_GETS_NOTIFICATION_EMAILS}),
        label=_("Receive notification emails?"),
        required=False,
    )

    class Meta:
        """Meta class for UserProfileForm."""

        model = User
        fields = ("gets_notification_emails", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AsyncPasswordResetForm(PasswordResetForm):
    """Form for resetting a user's password."""

    def send_mail(
        self,
        subject_template_name: str,
        email_template_name: str,
        context: dict[str, Any],
        from_email: Optional[str],
        to_email: str,
        html_email_template_name: Optional[str] = None,
    ) -> None:
        """Override parent method to send password reset email asynchronously using django_rq."""
        send_password_reset_email.delay(
            context=context,
        )


class UserContactInfoForm(ContactInfoFormMixin, forms.ModelForm):
    """ModelForm version of ContactInfoFormMixin for editing a User's contact information."""

    class Meta:
        """Meta class for UserContactInfoForm."""

        model = User
        fields: ClassVar[list[str]] = [
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "province_or_state",
            "other_province_or_state",
            "postal_or_zip_code",
            "country",
        ]

    def clean(self) -> dict:
        """Clean form data."""
        super().clean()
        return self.clean_address_fields()
