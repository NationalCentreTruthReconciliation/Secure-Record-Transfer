from typing import Any, ClassVar

from django import forms
from django.utils.translation import gettext_lazy as _

from recordtransfer.constants import (
    ID_SUBMISSION_GROUP_DESCRIPTION,
    ID_SUBMISSION_GROUP_NAME,
)
from recordtransfer.models import SubmissionGroup


class SubmissionGroupForm(forms.ModelForm):
    """Form for creating and updating SubmissionGroup instances."""

    required_css_class = 'required-field'

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Enter group name", "id": ID_SUBMISSION_GROUP_NAME}
        ),
        label="Group Name",
        required=True,
        label_suffix="",
    )
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Enter group description", "id": ID_SUBMISSION_GROUP_DESCRIPTION}
        ),
        label="Group Description",
        required=False,
        label_suffix="",
    )

    class Meta:
        """Meta options for SubmissionGroupForm."""

        model = SubmissionGroup
        fields: ClassVar[list[str]] = ["name", "description"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

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

        # Check if a SubmissionGroup with the same name already exists for the user
        if (
            SubmissionGroup.objects.filter(name=name, created_by=self.user)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError(
                {
                    "name": [
                        _("You have already created a group with this name."),
                    ]
                }
            )

        if not self.has_changed():
            raise forms.ValidationError(_("No changes detected."))

        return cleaned_data

    def save(self, commit: bool = True) -> SubmissionGroup:
        """Save the form data to a SubmissionGroup instance."""
        group = super().save(commit=False)
        group.created_by = self.user
        if commit:
            group.save()

        return group
