from typing import Any, ClassVar

from django import forms
from django.utils.translation import gettext_lazy as _

from recordtransfer.models import SubmissionGroup


class SubmissionGroupForm(forms.ModelForm):
    """Form for creating and updating SubmissionGroup instances."""

    name = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Enter group name"}),
        label="Group Name",
        required=True,
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Enter group description"}),
        label="Group Description",
        required=False,
    )

    class Meta:
        """Meta options for SubmissionGroupForm."""

        model = SubmissionGroup
        fields: ClassVar[list[str]] = ["name", "description"]

    def clean(self) -> "dict[str, Any]":
        """Clean the form data."""
        if not self.data:
            raise forms.ValidationError(_("Form is empty."))

        cleaned_data = super().clean()
        name = cleaned_data.get("name")

        if not name:
            raise forms.ValidationError(
                {
                    "name": [
                        _("Required"),
                    ]
                }
            )

        if not self.has_changed():
            raise forms.ValidationError(_("No changes detected."))

        return cleaned_data
