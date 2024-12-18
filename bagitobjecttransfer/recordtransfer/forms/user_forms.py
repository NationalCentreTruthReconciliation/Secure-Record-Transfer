from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from recordtransfer.constants import (
    ID_CONFIRM_NEW_PASSWORD,
    ID_CURRENT_PASSWORD,
    ID_FIRST_NAME,
    ID_GETS_NOTIFICATION_EMAILS,
    ID_LAST_NAME,
    ID_NEW_PASSWORD,
)
from recordtransfer.models import User

import re

class UserProfileForm(forms.ModelForm):
    """Form for editing user profile."""
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"id": ID_FIRST_NAME}),
        label=_("First Name"),
        required=True,
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"id": ID_LAST_NAME}),
        label=_("Last Name"),
        required=True,
    )
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

    NAME_PATTERN = re.compile(r"^(?!.*[.\s']{2})[A-Za-z\s.'-]+$")

    class Meta:
        """Meta class for UserProfileForm."""

        model = User
        fields = ("gets_notification_emails", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        user:User = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["gets_notification_emails"].initial = user.gets_notification_emails


    def clean(self) -> "dict[str, Any]":
        """Clean the form data."""
        if not self.data:
            raise ValidationError(_("Form is empty."))

        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if first_name and not self.NAME_PATTERN.match(first_name):
            raise ValidationError(
            {
                "first_name": [
                _("Invalid first name."),
                ]
            }
            )

        if last_name and not self.NAME_PATTERN.match(last_name):
            raise ValidationError(
            {
                "last_name": [
                _("Invalid last name."),
                ]
            }
            )

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

        if not self.has_changed() and not password_change:
            raise ValidationError(_("No fields have been changed."))

        return cleaned_data

    def save(self, commit: bool = True) -> User:
        """Save the form data."""
        user: User = super().save(commit=False)

        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)

        gets_notification_emails = self.cleaned_data.get("gets_notification_emails")
        if gets_notification_emails is not None:
            user.gets_notification_emails = gets_notification_emails
        
        # First and last name always get updated since they are required fields
        user.first_name = self.cleaned_data.get("first_name", user.first_name)
        user.last_name = self.cleaned_data.get("last_name", user.last_name)

        if commit:
            user.save()
        return user
