"""Forms specific to the recordtransfer admin site."""

from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.utils.html import format_html
from django.utils.translation import gettext

from recordtransfer.forms.mixins import ContactInfoFormMixin
from recordtransfer.models import (
    Submission,
    User,
)


class UserAdminForm(ContactInfoFormMixin, UserChangeForm):
    """Custom form for User admin that includes contact information fields."""

    class Meta:
        """Meta class for UserAdminForm."""

        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make contact info fields not required for admin
        for field_name in [
            "phone_number",
            "address_line_1",
            "city",
            "province_or_state",
            "postal_or_zip_code",
            "country",
        ]:
            if field_name in self.fields:
                self.fields[field_name].required = False

    def clean(self) -> dict[str, Any]:
        """Override clean to call both parent clean methods and enforce group validation."""
        cleaned_data = super().clean()

        # Required contact fields that must all be present if any are present
        required_contact_fields = [
            "phone_number",
            "address_line_1",
            "city",
            "province_or_state",
            "postal_or_zip_code",
            "country",
        ]

        # All contact fields (including optional ones)
        all_contact_fields = [
            *required_contact_fields,
            "address_line_2",
            "other_province_or_state",
        ]

        # Check if any contact field has a value
        has_any_contact_data = any(cleaned_data.get(field) for field in all_contact_fields)

        if has_any_contact_data:
            # If any contact field is filled, all required fields must be filled
            for field_name in required_contact_fields:
                if not cleaned_data.get(field_name):
                    self.add_error(
                        field_name,
                        gettext("This field is required when contact information is provided."),
                    )

            # Additional validation for address fields
            self.clean_address_fields()

        return cleaned_data


class RecordTransferModelForm(forms.ModelForm):
    """Adds disabled_fields to forms.ModelForm."""

    disabled_fields: ClassVar[list] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and instance.pk and self.disabled_fields:
            # Disable fields
            for field in self.disabled_fields:
                if field in self.fields:
                    self.fields[field].disabled = True


class SubmissionModelForm(RecordTransferModelForm):
    """Form for editing Submissions."""

    class Meta:
        """Meta class for SubmissionModelForm."""

        model = Submission
        fields = (
            "metadata",
            "user",
            "upload_session",
            "part_of_group",
            "uuid",
        )

    disabled_fields: ClassVar[list] = [
        "metadata",
        "upload_session",
        "user",
        "part_of_group",
        "uuid",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, "instance") and self.instance.metadata:
            # TODO: This makes the tiny link by the Metadata title in the Submission form.
            self.fields["metadata"].help_text = " | ".join(
                [
                    format_html('<a href="{}">{}</a>', url, gettext(text))
                    for url, text in [
                        (self.instance.get_admin_metadata_change_url(), "View or Change Metadata"),
                    ]
                ]
            )
        self.fields["metadata"].widget.can_add_related = False
