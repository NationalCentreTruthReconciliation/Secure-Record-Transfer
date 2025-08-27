import re
from datetime import datetime
from typing import ClassVar, Optional

from django import forms
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from caais.constants import ACCESSION_IDENTIFIER_TYPE
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
        self.fields["date_of_materials"].help_text = gettext(
            "%(help_text)s. Use the date format YYYY-MM-DD for a single date or YYYY-MM-DD - YYYY-MM-DD for a "
            "date range"
        ) % {"help_text": original_help_text}

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
        """Form date as approximate if user chose to mark the date as approximate."""
        cleaned_data = super().clean()

        if date := cleaned_data.get("date_of_materials"):
            self._validate_date_format_and_parse(date, cleaned_data)

        return cleaned_data

    def _validate_date_format_and_parse(self, date: str, cleaned_data: dict) -> None:
        """Validate date format and parse dates."""
        match_obj = re.match(MetadataForm.DATE_REGEX, date)

        if match_obj is None:
            self.add_error("date_of_materials", _("Invalid date format"))
            return

        raw_start_date = match_obj.group("start_date")
        raw_end_date = match_obj.group("end_date") if match_obj.group("end_date") else None

        start_date = self._validate_single_date(raw_start_date, "start")
        end_date = self._validate_single_date(raw_end_date, "end") if raw_end_date else None

        if start_date and end_date:
            self._validate_date_range(start_date, end_date, raw_start_date, cleaned_data)

    def _validate_single_date(self, raw_date: str, date_type: str) -> Optional[datetime]:
        """Validate a single date string and return parsed date."""
        try:
            parsed_date = datetime.strptime(raw_date, r"%Y-%m-%d")

            if parsed_date.date() > datetime.now().date():
                error_msg = (
                    _("Date cannot be in the future")
                    if date_type == "start"
                    else _("End date cannot be in the future")
                )
                self.add_error("date_of_materials", error_msg)

            if parsed_date.date() < datetime(1800, 1, 1).date():
                error_msg = (
                    _("Date cannot be before 1800")
                    if date_type == "start"
                    else _("End date cannot be before 1800")
                )
                self.add_error("date_of_materials", error_msg)

            return parsed_date

        except ValueError:
            error_msg = (
                _("Invalid date format")
                if date_type == "start"
                else _("Invalid date format for end date")
            )
            self.add_error("date_of_materials", error_msg)
            return None

    def _validate_date_range(
        self, start_date: datetime, end_date: datetime, raw_start_date: str, cleaned_data: dict
    ) -> None:
        """Validate date range constraints."""
        if end_date < start_date:
            self.add_error("date_of_materials", _("End date must be later than start date"))

        if end_date == start_date:
            cleaned_data["date_of_materials"] = raw_start_date

    def save(self, commit: bool = True) -> Metadata:
        """Save the accession identifier input as an Identifier on the metadata object.

        The Identifier is given the reserved type identified by ACCESSION_IDENTIFIER_TYPE.
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
                identifier_type=ACCESSION_IDENTIFIER_TYPE,
                identifier_value=accession_id,
            )

            new_id.save()

        else:
            metadata.update_accession_id(accession_id)

        return metadata


class InlineIdentifierForm(CaaisModelForm):
    """Form for inline editing of Identifier instances."""

    class Meta:
        """Meta options for the form."""

        model = Identifier
        fields = "__all__"

        required = ("identifier_value",)

        widgets: ClassVar = {
            "identifier_note": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField enable-vertical-resize",
                }
            ),
        }

    def clean(self) -> dict:
        """Don't allow a duplicate accession identifier to be specified."""
        cleaned_data = super().clean()
        id_type = cleaned_data.get("identifier_type", "")
        if id_type.lower() == ACCESSION_IDENTIFIER_TYPE.lower():
            self.add_error(
                "identifier_type",
                _("'%(id)s' is a reserved Identifier type - please use another type name")
                % {"id": id_type},
            )
        return cleaned_data


class InlineArchivalUnitForm(CaaisModelForm):
    """Form for inline editing of ArchivalUnit instances."""

    class Meta:
        """Meta options for the form."""

        model = ArchivalUnit
        fields = "__all__"

        widgets: ClassVar = {
            "archival_unit": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineDispositionAuthorityForm(CaaisModelForm):
    """Form for inline editing of DispositionAuthority instances."""

    class Meta:
        """Meta options for the form."""

        model = DispositionAuthority
        fields = "__all__"

        widgets: ClassVar = {
            "disposition_authority": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineSourceOfMaterialForm(CaaisModelForm):
    """Form for inline editing of SourceOfMaterial instances."""

    class Meta:
        """Meta options for the form."""

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

        widgets: ClassVar = {
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
    """Form for inline editing of PreliminaryCustodialHistory instances."""

    class Meta:
        """Meta options for the form."""

        model = PreliminaryCustodialHistory
        fields = "__all__"

        widgets: ClassVar = {
            "preliminary_custodial_history": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineExtentStatementForm(CaaisModelForm):
    """Form for inline editing of ExtentStatement instances."""

    class Meta:
        """Meta options for the form."""

        model = ExtentStatement
        fields = "__all__"

        required = ("quantity_and_unit_of_measure",)

        not_required = (
            "extent_type",
            "content_type",
            "carrier_type",
        )

        widgets: ClassVar = {
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
    """Form for inline editing of PreliminaryScopeAndContent instances."""

    class Meta:
        """Meta options for the form."""

        model = PreliminaryScopeAndContent
        fields = "__all__"

        widgets: ClassVar = {
            "preliminary_scope_and_content": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineLanguageOfMaterialForm(CaaisModelForm):
    """Form for inline editing of LanguageOfMaterial instances."""

    class Meta:
        """Meta options for the form."""

        model = LanguageOfMaterial
        fields = "__all__"

        widgets: ClassVar = {
            "language_of_material": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineStorageLocationForm(CaaisModelForm):
    """Form for inline editing of StorageLocation instances."""

    class Meta:
        """Meta options for the form."""

        model = StorageLocation
        fields = "__all__"

        widgets: ClassVar = {
            "storage_location": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }


class InlineRightsForm(CaaisModelForm):
    """Form for inline editing of Rights instances."""

    class Meta:
        """Meta options for the form."""

        model = Rights
        fields = "__all__"

        required = ("rights_value",)

        not_required = ("rights_type",)

        widgets: ClassVar = {
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
    """Form for inline editing of PreservationRequirements instances."""

    class Meta:
        """Meta options for the form."""

        model = PreservationRequirements
        fields = "__all__"

        required = ("preservation_requirements_value",)

        not_required = ("preservation_requirements_type",)

        widgets: ClassVar = {
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
    """Form for inline editing of Appraisal instances."""

    class Meta:
        """Meta options for the form."""

        model = Appraisal
        fields = "__all__"

        required = ("appraisal_value",)

        not_required = ("appraisal_type",)

        widgets: ClassVar = {
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
    """Form for inline editing of AssociatedDocumentation instances."""

    class Meta:
        """Meta options for the form."""

        model = AssociatedDocumentation
        fields = "__all__"

        required = ("associated_documentation_title",)

        not_required = ("associated_documentation_type",)

        widgets: ClassVar = {
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
    """Form for inline editing of GeneralNote instances."""

    class Meta:
        """Meta options for the form."""

        model = GeneralNote
        fields = "__all__"

        widgets: ClassVar = {
            "general_note": forms.widgets.Textarea(
                attrs={
                    "rows": 2,
                    "class": "inline-textarea enable-vertical-resize",
                }
            )
        }
