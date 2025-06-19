import re
from typing import Any, ClassVar, Optional

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField

from recordtransfer.constants import HtmlIds
from recordtransfer.forms.mixins import ContactInfoFormMixin
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

    captcha = ReCaptchaField()


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile."""

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
        required=True,
        error_messages={
            "required": _("First name is required."),
            "invalid": _(NAME_VALIDATION_MESSAGE),
        },
    )
    last_name = forms.RegexField(
        regex=NAME_PATTERN,
        widget=forms.TextInput(attrs={"id": HtmlIds.ID_LAST_NAME}),
        label=_("Last Name"),
        required=True,
        error_messages={
            "required": _("Last name is required."),
            "invalid": _(NAME_VALIDATION_MESSAGE),
        },
    )
    gets_notification_emails = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"id": HtmlIds.ID_GETS_NOTIFICATION_EMAILS}),
        label=_("Receive notification emails?"),
        required=False,
    )
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": HtmlIds.ID_CURRENT_PASSWORD}),
        label=_("Current Password"),
        required=False,
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": HtmlIds.ID_NEW_PASSWORD}),
        label=_("New Password"),
        required=False,
        validators=[password_validation.validate_password],
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": HtmlIds.ID_CONFIRM_NEW_PASSWORD}),
        label=_("Confirm New Password"),
        required=False,
    )

    class Meta:
        """Meta class for UserProfileForm."""

        model = User
        fields = ("gets_notification_emails", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _validate_password_change(
        self,
        current_password: Optional[str],
        new_password: Optional[str],
        confirm_new_password: Optional[str],
    ) -> None:
        """Validate password change fields."""
        if not current_password:
            raise ValidationError(
                {
                    "current_password": [
                        _("Required"),
                    ]
                }
            )
        if not new_password:
            raise ValidationError(
                {
                    "new_password": [
                        _("Required"),
                    ]
                }
            )
        if not confirm_new_password:
            raise ValidationError(
                {
                    "confirm_new_password": [
                        _("Required"),
                    ]
                }
            )

        if new_password != confirm_new_password:
            raise ValidationError(
                {
                    "confirm_new_password": [
                        _("The new passwords do not match."),
                    ]
                }
            )

        if new_password == current_password:
            raise ValidationError(
                {
                    "new_password": [
                        _("The new password must be different from the current password."),
                    ]
                }
            )

        if not self.instance.check_password(current_password):
            raise ValidationError(
                {
                    "current_password": [
                        _("Password is incorrect."),
                    ]
                }
            )

    def clean(self) -> dict[str, Any]:
        """Clean the form data."""
        if not self.data:
            raise ValidationError(_("Form is empty."))

        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        password_change = bool(current_password or new_password or confirm_new_password)

        if password_change:
            self._validate_password_change(current_password, new_password, confirm_new_password)

        if not self.has_changed() and not password_change:
            raise ValidationError(_("No fields have been changed."))

        return cleaned_data

    def save(self, commit: bool = True) -> User:
        """Save the form data."""
        user: User = super().save(commit=False)

        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)

        if commit:
            user.save()
        return user

    def reset_form(self) -> None:
        """Reset form fields to initial values from instance."""
        if self.instance:
            self.data = self.data.copy()
            self.data["first_name"] = self.instance.first_name
            self.data["last_name"] = self.instance.last_name
            self.data["gets_notification_emails"] = self.instance.gets_notification_emails
            self.data["current_password"] = ""
            self.data["new_password"] = ""
            self.data["confirm_new_password"] = ""


class ProfileContactInfoForm(ContactInfoFormMixin, forms.ModelForm):
    """ModelForm version of ContactInfoFormMixin for profile editing."""

    class Meta:
        """Meta class for ProfileContactInfoForm."""

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
        cleaned_data = self.clean_address_fields()
        return cleaned_data
