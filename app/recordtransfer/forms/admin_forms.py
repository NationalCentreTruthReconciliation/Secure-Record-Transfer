"""Forms specific to the recordtransfer admin site."""

from typing import Any, ClassVar

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from recordtransfer.enums import SiteSettingKey, SiteSettingType
from recordtransfer.forms.mixins import ContactInfoFormMixin
from recordtransfer.models import (
    SiteSetting,
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


class SiteSettingModelForm(RecordTransferModelForm):
    """Form for editing SiteSettings with validation for different value types."""

    class Meta:
        """Meta class for SiteSettingModelForm."""

        model = SiteSetting
        fields = ("value",)

    disabled_fields: ClassVar[list] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.key:
            try:
                key_enum = SiteSettingKey[self.instance.key]
                description = getattr(key_enum, "description", "")
                if description:
                    self.fields["value"].help_text = mark_safe(
                        description.replace("\n", "<br><br>")
                    )
                else:
                    self.fields["value"].help_text = "No description available for this setting."
            except KeyError:
                self.fields["value"].help_text = "No description available for this setting."

    def clean_value(self) -> Any:
        """Validate the value field based on the selected value_type."""
        value = self.cleaned_data.get("value")
        value_type = self.instance.value_type

        if value_type == SiteSettingType.STR:
            if not isinstance(value, str):
                raise ValidationError("Value must be a text value.")
            if not value.strip():
                raise ValidationError("Value must be a non-empty text value.")

        elif value_type == SiteSettingType.INT:
            if not isinstance(value, str):
                raise ValidationError("Value must be a number.")

            try:
                int(value)
            except (ValueError, TypeError) as exc:
                raise ValidationError(
                    f"Value must be a valid whole number. '{value}' is not a valid number."
                ) from exc

        return value

    def clean(self) -> dict[str, Any]:
        """Additional form-level validation."""
        cleaned_data = super().clean()

        try:
            key = SiteSettingKey[self.instance.key]
        except KeyError as exc:
            raise ValidationError(f"Invalid setting key: {self.instance.key}") from exc

        value = cleaned_data.get("value")

        if key == SiteSettingKey.PAGINATE_BY:
            try:
                paginate_by = int(cleaned_data.get("value", 0))
                if paginate_by <= 0:
                    raise ValidationError(
                        f"{SiteSettingKey.PAGINATE_BY.key_name} must be a positive whole number."
                    )
            except (ValueError, TypeError) as exc:
                raise ValidationError(
                    f"{SiteSettingKey.PAGINATE_BY.key_name} must be a positive whole number."
                ) from exc
        elif key == SiteSettingKey.ARCHIVIST_EMAIL:
            value = cleaned_data.get("value", "")
            try:
                validate_email(value)
            except ValidationError as exc:
                raise ValidationError(
                    f"{SiteSettingKey.ARCHIVIST_EMAIL.key_name} must be a valid email address."
                ) from exc

        return cleaned_data
