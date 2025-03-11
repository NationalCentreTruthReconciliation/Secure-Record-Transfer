import re
from datetime import datetime
from typing import ClassVar

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from django_countries.fields import CountryField

from caais.models import (
    AbstractTerm,
    Appraisal,
    ArchivalUnit,
    AssociatedDocumentation,
    DispositionAuthority,
    ExtentStatement,
    GeneralNote,
    Identifier,
    LanguageOfMaterial,
    Metadata,
    PreliminaryCustodialHistory,
    PreliminaryScopeAndContent,
    PreservationRequirements,
    Rights,
    SourceOfMaterial,
    StorageLocation,
)
from caais.widgets import CustomCountrySelectWidget, DateIsApproximateWidget, DateOfMaterialsWidget

SelectTermWidget = forms.widgets.Select(
    attrs={
        "class": "vTextField",
    }
)


class CaaisModelForm(forms.ModelForm):
    """Form for CAAIS models. Automatically adds term help_text on all term
    fields since it is not populated by default.

    Allows the specification of 'required' and 'not_required' fields to override
    the default form behaviour.

    Also allows the specification of 'disabled' fields to disable specific
    fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_term_fields()
        self._set_required()
        self._set_not_required()
        self._set_disabled()

    def _update_term_fields(self):
        for field_name in self.fields:
            field = self.fields[field_name]
            if hasattr(field, "queryset"):
                model = field.queryset.model
                if issubclass(model, AbstractTerm):
                    field.help_text = model._meta.get_field("name").help_text

    def _set_required(self):
        if not hasattr(self.Meta, "required"):
            return
        for field_name in self.Meta.required:
            field = self.fields.get(field_name, None)
            if field is not None:
                field.required = True

    def _set_not_required(self):
        if not hasattr(self.Meta, "not_required"):
            return
        for field_name in self.Meta.not_required:
            field = self.fields.get(field_name, None)
            if field is not None:
                field.required = False

    def _set_disabled(self):
        if not hasattr(self.Meta, "disabled"):
            return
        for field_name in self.Meta.disabled:
            field = self.fields.get(field_name, None)
            if field is not None:
                field.disabled = True


class MetadataForm(CaaisModelForm):
    """Form for Metadata model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            accession_id = self.instance.accession_identifier
            self.fields["accession_identifier"].initial = accession_id

        # Append to the help_text for date_of_materials provided by the Metadata model
        original_help_text = self.fields["date_of_materials"].help_text
        self.fields["date_of_materials"].help_text = (
            original_help_text
            + gettext(". Use the date format YYYY-MM-DD for a single date or YYYY-MM-DD - YYYY-MM-DD for a "
            "date range")
        )

    class Meta:
        """MetadataForm Meta class."""

        model = Metadata
        fields = (
            "accession_title",
            "date_of_materials",
            "date_is_approximate",
            "accession_identifier",
            "repository",
            "acquisition_method",
            "status",
            "date_of_materials",
            "rules_or_conventions",
            "language_of_accession_record",
        )

        required = (
            "accession_title",
            "date_of_materials",
            "accession_identifier",
        )

        not_required = (
            "acquisition_method",
            "status",
        )

        widgets: ClassVar = {
            "acquisition_method": SelectTermWidget,
            "status": SelectTermWidget,
            "date_of_materials": DateOfMaterialsWidget,
            "date_is_approximate": DateIsApproximateWidget,
        }

    accession_identifier = forms.CharField(
        max_length=128,
        required=True,
        help_text="Record an identifier to uniquely identify this accession",
        widget=forms.widgets.TextInput(
            attrs={
                "class": "vTextField",
            }
        ),
    )

    DATE_REGEX = (
        r"^(?P<start_date>\d{4}-\d{2}-\d{2})"
        r"(?:\s-\s"
        r"(?P<end_date>\d{4}-\d{2}-\d{2})"
        r")?$"
    )

    def clean(self) -> dict:
        """Validate the date_of_materials field."""
        cleaned_data = super().clean()

        if date := cleaned_data.get("date_of_materials"):
            match_obj = re.match(MetadataForm.DATE_REGEX, date)

            if match_obj is None:
                self.add_error("date_of_materials", gettext("Invalid date format"))
                return cleaned_data

            raw_start_date = match_obj.group("start_date")

            try:
                raw_end_date = match_obj.group("end_date")
            except IndexError:
                raw_end_date = None

            invalid_date_message_added = False
            future_date_message_added = False
            early_date_message_added = False

            start_date = None

            try:
                start_date = datetime.strptime(raw_start_date, r"%Y-%m-%d").date()

                if start_date > datetime.now().date():
                    self.add_error("date_of_materials", gettext("Date cannot be in the future"))
                    future_date_message_added = True

                if start_date < datetime(1800, 1, 1).date():
                    self.add_error("date_of_materials", gettext("Date cannot be before 1800"))
                    early_date_message_added = True

            except ValueError:
                self.add_error("date_of_materials", gettext("Invalid date format"))
                invalid_date_message_added = True

            end_date = None
            if raw_end_date:
                try:
                    end_date = datetime.strptime(raw_end_date, r"%Y-%m-%d").date()

                    if not future_date_message_added and end_date > datetime.now().date():
                        self.add_error(
                            "date_of_materials", gettext("End date cannot be in the future")
                        )

                    if not early_date_message_added and end_date < datetime(1800, 1, 1).date():
                        self.add_error(
                            "date_of_materials", gettext("End date cannot be before 1800")
                        )

                except ValueError:
                    if not invalid_date_message_added:
                        self.add_error(
                            "date_of_materials", gettext("Invalid date format for end date")
                        )

            if end_date and start_date:
                if end_date < start_date:
                    self.add_error(
                        "date_of_materials",
                        gettext("End date must be later than start date"),
                    )

                if end_date == start_date:
                    cleaned_data["date_of_materials"] = raw_start_date

        return cleaned_data

    def save(self, commit: bool = True) -> Metadata:
        """Save the accession identifier input as an Identifier on the metadata object.

        The Identifier is given the reserved name "Accession Identifier".
        """
        metadata: Metadata = super().save(commit)

        accession_id = self.cleaned_data["accession_identifier"]

        # No changes required - return early
        if not accession_id or accession_id == metadata.accession_identifier:
            return metadata

        # The metadata needs to be saved before updating the accession identifier if it hasn't
        # already been saved
        if commit and not metadata.pk:
            metadata.save()

        if not metadata.accession_identifier:
            new_id = Identifier(
                metadata=metadata,
                identifier_type="Accession Identifier",
                identifier_value=accession_id,
            )

            new_id.save()

        else:
            metadata.update_accession_id(accession_id)

        return metadata


class InlineIdentifierForm(CaaisModelForm):
    class Meta:
        model = Identifier
        fields = "__all__"

        required = ("identifier_value",)

        widgets = {
            "identifier_note": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }

    def clean_identifier_type(self):
        """Don't allow a duplicate accession identifier to be specified"""
        data = self.cleaned_data["identifier_type"]
        if data.lower() == "accession identifier":
            raise ValidationError(
                f"{data} is a reserved Identifier type - please use another type name"
            )
        return data


class InlineArchivalUnitForm(CaaisModelForm):
    class Meta:
        model = ArchivalUnit
        fields = "__all__"

        widgets = {
            "archival_unit": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineDispositionAuthorityForm(CaaisModelForm):
    class Meta:
        model = DispositionAuthority
        fields = "__all__"

        widgets = {
            "disposition_authority": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineSourceOfMaterialForm(CaaisModelForm):
    class Meta:
        model = SourceOfMaterial
        fields = "__all__"

        required = (
            "source_name",
            "email_address",
        )

        not_required = (
            "phone_number",
            "source_type",
            "source_role",
            "source_confidentiality",
        )

        widgets = {
            "source_type": SelectTermWidget,
            "source_role": SelectTermWidget,
            "source_note": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
            "source_confidentiality": SelectTermWidget,
        }

    phone_number = forms.RegexField(
        regex=r"^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$",
        error_messages={
            "required": gettext("This field is required."),
            "invalid": gettext('Phone number must look like "+1 (999) 999-9999"'),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "+1 (999) 999-9999",
                "class": "vTextField",
            }
        ),
        label=gettext("Phone number"),
    )

    email_address = forms.EmailField(
        label=gettext("Email"),
        widget=forms.TextInput(
            attrs={
                "placeholder": "person@example.com",
                "class": "vTextField",
            }
        ),
    )

    country = CountryField(blank_label=gettext("Select a Country")).formfield(
        required=False,
        widget=CustomCountrySelectWidget(
            attrs={
                "class": "vTextField",
            }
        ),
    )


class InlinePreliminaryCustodialHistoryForm(CaaisModelForm):
    class Meta:
        model = PreliminaryCustodialHistory
        fields = "__all__"

        widgets = {
            "preliminary_custodial_history": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineExtentStatementForm(CaaisModelForm):
    class Meta:
        model = ExtentStatement
        fields = "__all__"

        required = ("quantity_and_unit_of_measure",)

        not_required = (
            "extent_type",
            "content_type",
            "carrier_type",
        )

        widgets = {
            "extent_type": SelectTermWidget,
            "quantity_and_unit_of_measure": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
            "content_type": SelectTermWidget,
            "carrier_type": SelectTermWidget,
            "extent_note": forms.widgets.Textarea(
                attrs={
                    "rows": 1,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }


class InlinePreliminaryScopeAndContentForm(CaaisModelForm):
    class Meta:
        model = PreliminaryScopeAndContent
        fields = "__all__"

        widgets = {
            "preliminary_scope_and_content": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineLanguageOfMaterialForm(CaaisModelForm):
    class Meta:
        model = LanguageOfMaterial
        fields = "__all__"

        widgets = {
            "language_of_material": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineStorageLocationForm(CaaisModelForm):
    class Meta:
        model = StorageLocation
        fields = "__all__"

        widgets = {
            "storage_location": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineRightsForm(CaaisModelForm):
    class Meta:
        model = Rights
        fields = "__all__"

        required = ("rights_value",)

        not_required = ("rights_type",)

        widgets = {
            "rights_type": SelectTermWidget,
            "rights_value": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
            "rights_note": forms.widgets.Textarea(
                attrs={
                    "rows": 1,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }


class InlinePreservationRequirementsForm(CaaisModelForm):
    class Meta:
        model = PreservationRequirements
        fields = "__all__"

        required = ("preservation_requirements_value",)

        not_required = ("preservation_requirements_type",)

        widgets = {
            "preservation_requirements_type": SelectTermWidget,
            "preservation_requirements_value": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
            "preservation_requirements_note": forms.widgets.Textarea(
                attrs={
                    "rows": 1,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }


class InlineAppraisalForm(CaaisModelForm):
    class Meta:
        model = Appraisal
        fields = "__all__"

        required = ("appraisal_value",)

        not_required = ("appraisal_type",)

        widgets = {
            "appraisal_type": SelectTermWidget,
            "appraisal_value": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
            "appraisal_note": forms.widgets.Textarea(
                attrs={
                    "rows": 1,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }


class InlineAssociatedDocumentationForm(CaaisModelForm):
    class Meta:
        model = AssociatedDocumentation
        fields = "__all__"

        required = ("associated_documentation_title",)

        not_required = ("associated_documentation_type",)

        widgets = {
            "associated_documentation_type": SelectTermWidget,
            "associated_documentation_value": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
            "associated_documentation_note": forms.widgets.Textarea(
                attrs={
                    "rows": 1,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }


class InlineGeneralNoteForm(CaaisModelForm):
    class Meta:
        model = GeneralNote
        fields = "__all__"

        widgets = {
            "general_note": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }
