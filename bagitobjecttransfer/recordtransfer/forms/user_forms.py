from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from recordtransfer.constants import (
    ID_CONFIRM_NEW_PASSWORD,
    ID_CURRENT_PASSWORD,
    ID_GETS_NOTIFICATION_EMAILS,
    ID_NEW_PASSWORD,
)
from recordtransfer.models import User


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile."""

    gets_notification_emails = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"id": ID_GETS_NOTIFICATION_EMAILS}),
        label=_("Receive notification emails?"),
        required=False,
    )
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": ID_CURRENT_PASSWORD}),
        label=_("Current Password"),
        required=False,
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": ID_NEW_PASSWORD}),
        label=_("New Password"),
        required=False,
        validators=[password_validation.validate_password],
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"id": ID_CONFIRM_NEW_PASSWORD}),
        label=_("Confirm New Password"),
        required=False,
    )

    class Meta:
        """Meta class for UserProfileForm."""

        model = User
        fields = ("gets_notification_emails",)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["gets_notification_emails"].initial = user.gets_notification_emails

    def clean(self) -> "dict[str, Any]":
        """Clean the form data."""
        if not self.data:
            raise ValidationError(_("Form is empty."))

        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")
        gets_notification_emails = cleaned_data.get("gets_notification_emails")

        password_change = False

        if current_password or new_password or confirm_new_password:
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

            password_change = True

        notification_setting_changed = self.has_changed()
        if not notification_setting_changed and not password_change:
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
