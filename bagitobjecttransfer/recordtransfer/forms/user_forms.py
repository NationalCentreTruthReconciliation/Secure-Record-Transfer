from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.utils.translation import ugettext_lazy as _

from recordtransfer.models import User


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile."""

    gets_notification_emails = forms.BooleanField(
        required=False, label=_("Receive notification emails?")
    )
    current_password = forms.CharField(
        widget=forms.PasswordInput, label=_("Current Password"), required=False
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label=_("New Password"),
        required=False,
        validators=[password_validation.validate_password],
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput, label=_("Confirm New Password"), required=False
    )

    class Meta:
        """Meta class for UserProfileForm."""

        model = User
        fields = ("gets_notification_emails",)

    def clean(self) -> "dict[str, Any]":
        """Clean the form data."""
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if current_password or new_password or confirm_new_password:
            if not self.instance.check_password(current_password):
                self.add_error("current_password", _("Current password is incorrect."))
            if new_password != confirm_new_password:
                self.add_error(
                    "confirm_new_password", _("The new passwords do not match.")
                )

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
