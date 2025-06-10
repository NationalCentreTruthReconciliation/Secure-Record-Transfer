"""Forms specific to creating new submissions."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional, OrderedDict, TypedDict, Union
from uuid import UUID

from caais.models import RightsType, SourceRole, SourceType
from django import forms
from django.conf import settings
from django.db.models import Case, CharField, Value, When
from django.forms import BaseForm, BaseFormSet
from django.utils.translation import gettext
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible

from recordtransfer.constants import (
    HtmlIds,
    OtherValues,
)
from recordtransfer.enums import SubmissionStep
from recordtransfer.models import SubmissionGroup, UploadSession, User


class ReviewFormItem(TypedDict):
    """A dictionary representing a form item for review by the user.

    Attributes:
        step_title: The human-readable title of the step.
        step_name: The name of the step.
        fields: The fields of the step.
        note: An optional note, intended to be used as a message to the user if a section is empty,
        for example.
    """

    step_title: str
    step_name: str
    fields: Union[list[dict[str, Any]], dict[str, Any]]
    note: Optional[str]


class SubmissionForm(forms.Form):
    """Base form for all submission forms."""

    required_css_class = "required-field"


class AcceptLegal(SubmissionForm):
    """Form for accepting legal terms."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.ACCEPT_LEGAL

    def clean(self) -> dict:
        """Clean form data and validate the session token."""
        cleaned_data = super().clean()
        if not cleaned_data["agreement_accepted"]:
            self.add_error("agreement_accepted", "You must accept before continuing")
        return cleaned_data

    agreement_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(),
        label=gettext("I accept these terms"),
    )


class ContactInfoForm(SubmissionForm):
    """The Contact Information portion of the form. Contains fields from Section 2 of CAAIS."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.CONTACT_INFO

    def clean(self) -> dict:
        """Clean form data and ensure that the province_or_state field is filled out if 'Other'
        is.
        """
        cleaned_data = super().clean()
        region = cleaned_data.get("province_or_state")
        if not region or region.lower() == "":
            self.add_error(
                "province_or_state",
                'You must select a province or state, use "Other" to enter a custom location',
            )
        elif region.lower() == "other" and not cleaned_data["other_province_or_state"]:
            self.add_error(
                "other_province_or_state",
                'This field must be filled out if "Other" province or state is selected',
            )
        elif region.lower() != "other":
            cleaned_data["other_province_or_state"] = ""  # Clear this field since it's not needed
            self.fields["other_province_or_state"].label = "hidden"

        return cleaned_data

    contact_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        label=gettext("Contact name"),
    )

    job_title = forms.CharField(
        max_length=64,
        min_length=2,
        required=False,
        label=gettext("Job title"),
    )

    organization = forms.CharField(
        max_length=64,
        min_length=2,
        required=False,
        label=gettext("Organization"),
    )

    phone_number = forms.RegexField(
        regex=r"^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$",
        error_messages={
            "required": gettext("This field is required."),
            "invalid": gettext('Phone number must look like "+1 (999) 999-9999"'),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "+1 (999) 999-9999",
                "class": "reduce-form-field-width",
            }
        ),
        label=gettext("Phone number"),
    )

    email = forms.EmailField(
        label=gettext("Email"),
    )

    address_line_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": gettext("Street, and street number")}),
        label=gettext("Address line 1"),
    )

    address_line_2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": gettext("Unit Number, RPO, PO BOX... (optional)")}
        ),
        label=gettext("Address line 2"),
    )

    city = forms.CharField(
        max_length=100,
        required=True,
        label=gettext("City"),
    )

    province_or_state = forms.ChoiceField(
        required=True,
        widget=forms.Select(
            attrs={
                "id": HtmlIds.ID_CONTACT_INFO_PROVINCE_OR_STATE,
                "class": "reduce-form-field-width",
            }
        ),
        choices=[
            ("", gettext("Select your province")),
            # Canada
            ("Other", gettext(OtherValues.PROVINCE_OR_STATE)),
            ("AB", "Alberta"),
            ("BC", "British Columbia"),
            ("MB", "Manitoba"),
            ("NL", "Newfoundland and Labrador"),
            ("NT", "Northwest Territories"),
            ("NS", "Nova Scotia"),
            ("NU", "Nunavut"),
            ("ON", "Ontario"),
            ("PE", "Prince Edward Island"),
            ("QC", "Quebec"),
            ("SK", "Saskatchewan"),
            ("YT", "Yukon Territory"),
            # United States of America
            ("AL", "Alabama"),
            ("AK", "Arkansas"),
            ("AZ", "Arizona"),
            ("AR", "Arkanasas"),
            ("CA", "California"),
            ("CO", "Colorado"),
            ("CT", "Connecticut"),
            ("DE", "Delaware"),
            ("DC", "District of Columbia"),
            ("FL", "Florida"),
            ("GA", "Georgia"),
            ("HI", "Hawaii"),
            ("ID", "Idaho"),
            ("IL", "Illinois"),
            ("IN", "Indiana"),
            ("IA", "Iowa"),
            ("KS", "Kansas"),
            ("KY", "Kentucky"),
            ("LA", "Louisiana"),
            ("ME", "Maine"),
            ("MD", "Maryland"),
            ("MA", "Massachusetts"),
            ("MI", "Michigan"),
            ("MN", "Minnesota"),
            ("MS", "Mississippi"),
            ("MO", "Missouri"),
            ("MT", "Montana"),
            ("NE", "Nebraska"),
            ("NV", "Nevada"),
            ("NH", "New Hampshire"),
            ("NJ", "New Jersey"),
            ("NM", "New Mexico"),
            ("NY", "New York"),
            ("NC", "North Carolina"),
            ("ND", "North Dakota"),
            ("OH", "Ohio"),
            ("OK", "Oklahoma"),
            ("OR", "Oregon"),
            ("PA", "Pennsylvania"),
            ("RI", "Rhode Island"),
            ("SC", "South Carolina"),
            ("SD", "South Dakota"),
            ("TN", "Tennessee"),
            ("TX", "Texas"),
            ("UT", "Utah"),
            ("VT", "Vermont"),
            ("VA", "Virginia"),
            ("WA", "Washington"),
            ("WV", "West Virginia"),
            ("WI", "Wisconsin"),
            ("WY", "Wyoming"),
        ],
        initial="",
        label="Province or state",
    )

    other_province_or_state = forms.CharField(
        required=False,
        min_length=2,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                "id": HtmlIds.ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE,
                "class": "reduce-form-field-width",
            }
        ),
        label=gettext("Other province or state"),
    )

    postal_or_zip_code = forms.RegexField(
        regex=r"^(?:[0-9]{5}(?:-[0-9]{4})?)|(?:[A-Za-z]\d[A-Za-z][\- ]?\d[A-Za-z]\d)$",
        error_messages={
            "required": gettext("This field is required."),
            "invalid": gettext(
                'Postal code must look like "Z0Z 0Z0", zip code must look like '
                '"12345" or "12345-1234"'
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Z0Z 0Z0",
                "class": "reduce-form-field-width",
            }
        ),
        label=gettext("Postal / Zip code"),
    )

    country = CountryField(blank_label=gettext("Select your Country")).formfield(
        widget=CountrySelectWidget(
            attrs={
                "class": "reduce-form-field-width",
            }
        ),
        label=gettext("Country"),
    )


class SourceInfoForm(SubmissionForm):
    """The Source Information portion of the form. Contains fields from Section 2 of CAAIS.

    This form is nominally "optional," but a user can fill in the fields if they want to. The
    source name, source type, and source role are all required in CAAIS, so if a user chooses not
    to fill in the form, we use defaults from the initial data for those fields.
    """

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.SOURCE_INFO

    def __init__(self, *args, **kwargs):
        if "defaults" not in kwargs:
            raise ValueError(
                "SourceInfoForm requires default data (i.e., defaults should be a keyword "
                "argument)"
            )

        self.defaults = kwargs.pop("defaults")

        for required in ("source_name", "source_type", "source_role"):
            if required not in self.defaults:
                raise ValueError(f"SourceInfoForm requires a default value for {required}")

        self.default_source_name = self.defaults["source_name"]
        self.default_source_type = self.defaults["source_type"]
        self.default_source_role = self.defaults["source_role"]

        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        """Clean form and set defaults if the user chose not to enter source info manually."""
        cleaned_data = super().clean()

        # Set defaults if manual entry is not selected
        if cleaned_data["enter_manual_source_info"] == "no":
            cleaned_data.update(
                {
                    "source_name": self.default_source_name,
                    "source_type": self.default_source_type,
                    "source_role": self.default_source_role,
                    "other_source_type": "",
                    "other_source_role": "",
                    "source_note": "",
                    "preliminary_custodial_history": "",
                }
            )
            for field in ["other_source_type", "other_source_role"]:
                self.fields[field].label = "hidden"

        if not cleaned_data.get("source_name"):
            self.add_error("source_name", gettext("This field is required."))

        self._validate_source_type(cleaned_data)
        self._validate_source_role(cleaned_data)

        return cleaned_data

    def _validate_source_type(self, cleaned_data: dict[str, Any]) -> dict[str, Any]:
        """Validate the source type field."""
        source_type = cleaned_data.get("source_type")
        if not source_type:
            self.add_error("source_type", gettext("This field is required."))
        elif source_type.name.lower() == "other" and not cleaned_data.get("other_source_type"):
            self.add_error(
                "other_source_type",
                gettext('If "Source type" is Other, enter your own source type'),
            )
        elif source_type.name.lower() != "other":
            cleaned_data["other_source_type"] = ""
            self.fields["other_source_type"].label = "hidden"
        return cleaned_data

    def _validate_source_role(self, cleaned_data: dict[str, Any]) -> dict[str, Any]:
        """Validate the source role field."""
        source_role = cleaned_data.get("source_role")
        if not source_role:
            self.add_error("source_role", gettext("This field is required."))
        elif source_role.name.lower() == "other" and not cleaned_data.get("other_source_role"):
            self.add_error(
                "other_source_role",
                gettext('If "Source role" is Other, enter your own source role'),
            )
        elif source_role.name.lower() != "other":
            cleaned_data["other_source_role"] = ""
            self.fields["other_source_role"].label = "hidden"
        return cleaned_data

    enter_manual_source_info = forms.ChoiceField(
        choices=[
            ("yes", gettext("Yes")),
            ("no", gettext("No")),
        ],
        widget=forms.RadioSelect(
            attrs={"id": HtmlIds.ID_SOURCE_INFO_ENTER_MANUAL_SOURCE_INFO},
        ),
        label=gettext("Submitting on behalf of an organization/another person"),
        initial="no",
    )

    source_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=False,  # Required if enter_manual_source_info == "yes"
        widget=forms.TextInput(
            attrs={
                "class": "faux-required-field",
            }
        ),
        label=gettext("Name of source"),
        help_text=gettext("The organization or entity submitting the records"),
    )

    source_type = forms.ModelChoiceField(
        required=False,  # Required if enter_manual_source_info == "yes"
        queryset=SourceType.objects.all()
        .annotate(
            sort_order_other_first=Case(
                When(name__iexact="other", then=Value("____")),
                default="name",
                output_field=CharField(),
            )
        )
        .order_by("sort_order_other_first"),
        empty_label=gettext("Please select one"),
        label=gettext("Source type"),
        help_text=gettext(
            "How would you describe <b>what</b> the source entity is? "
            "i.e., The source is a(n) ______"
        ),
        widget=forms.Select(
            attrs={
                "class": "reduce-form-field-width faux-required-field",
                "id": HtmlIds.ID_SOURCE_INFO_SOURCE_TYPE,
            }
        ),
    )

    other_source_type = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": gettext("A source type not covered by the other choices"),
                "class": "faux-required-field",
                "id": HtmlIds.ID_SOURCE_INFO_OTHER_SOURCE_TYPE,
            }
        ),
        label=gettext("Other source type"),
    )

    source_role = forms.ModelChoiceField(
        required=False,  # Required if enter_manual_source_info == "yes"
        queryset=SourceRole.objects.all()
        .annotate(
            sort_order_other_first=Case(
                When(name__iexact="other", then=Value("____")),
                default="name",
                output_field=CharField(),
            )
        )
        .order_by("sort_order_other_first"),
        empty_label=gettext("Please select one"),
        label=gettext("Source role"),
        help_text=gettext("How does the source relate to the records? "),
        widget=forms.Select(
            attrs={
                "class": "reduce-form-field-width faux-required-field",
                "id": HtmlIds.ID_SOURCE_INFO_SOURCE_ROLE,
            }
        ),
    )

    other_source_role = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": gettext("A source role not covered by the other choices"),
                "class": "faux-required-field",
                "id": HtmlIds.ID_SOURCE_INFO_OTHER_SOURCE_ROLE,
            }
        ),
        label=gettext("Other source role"),
    )

    source_note = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": "4",
                "placeholder": gettext(
                    "Enter any notes you think may be useful for the archives to "
                    "have about this entity (optional)"
                ),
            }
        ),
        label=gettext("Source notes"),
        help_text=gettext("e.g., The donor wishes to remain anonymous"),
    )

    preliminary_custodial_history = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": "4",
                "placeholder": gettext(
                    "Enter any information you have on the history of who has had "
                    "custody of the records or who has kept the records in the past "
                    "(optional)"
                ),
            }
        ),
        label=gettext("Custodial history"),
        help_text=gettext("e.g., John Doe held these records before donating them in 1960"),
    )


class RecordDescriptionForm(SubmissionForm):
    """The Description Information portion of the form. Contains fields from Section 3 of CAAIS."""

    DATE_REGEX = (
        r"^(?P<start_date>\d{4}-\d{2}-\d{2})"
        r"(?:\s-\s"
        r"(?P<end_date>\d{4}-\d{2}-\d{2})"
        r")?$"
    )

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.RECORD_DESCRIPTION

    def clean(self) -> dict:
        """Form date as approximate if user chose to mark the date as approximate."""
        cleaned_data = super().clean()

        if date := cleaned_data.get("date_of_materials"):
            self._validate_date_format_and_parse(date, cleaned_data)

        return cleaned_data

    def _validate_date_format_and_parse(self, date: str, cleaned_data: dict) -> None:
        """Validate date format and parse dates."""
        match_obj = re.match(RecordDescriptionForm.DATE_REGEX, date)

        if match_obj is None:
            self.add_error("date_of_materials", gettext("Invalid date format"))
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
                    gettext("Date cannot be in the future")
                    if date_type == "start"
                    else gettext("End date cannot be in the future")
                )
                self.add_error("date_of_materials", error_msg)

            if parsed_date.date() < datetime(1800, 1, 1).date():
                error_msg = (
                    gettext("Date cannot be before 1800")
                    if date_type == "start"
                    else gettext("End date cannot be before 1800")
                )
                self.add_error("date_of_materials", error_msg)

            return parsed_date

        except ValueError:
            error_msg = (
                gettext("Invalid date format")
                if date_type == "start"
                else gettext("Invalid date format for end date")
            )
            self.add_error("date_of_materials", error_msg)
            return None

    def _validate_date_range(
        self, start_date: datetime, end_date: datetime, raw_start_date: str, cleaned_data: dict
    ) -> None:
        """Validate date range constraints."""
        if end_date < start_date:
            self.add_error("date_of_materials", gettext("End date must be later than start date"))

        if end_date == start_date:
            cleaned_data["date_of_materials"] = raw_start_date

    accession_title = forms.CharField(
        min_length=2,
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": gettext("e.g., Committee Meeting Minutes")}),
        label=gettext("Title"),
    )

    date_of_materials = forms.RegexField(
        regex=DATE_REGEX,
        min_length=10,
        max_length=23,
        required=True,
        error_messages={
            "required": gettext("This field is required."),
            "invalid": gettext("Date must be in the format YYYY-MM-DD or YYYY-MM-DD - YYYY-MM-DD"),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": gettext("2000-03-14 - 2001-05-06"),
                "class": "date-range-picker" if settings.USE_DATE_WIDGETS else "date-range-text",
                **({"readonly": "readonly"} if settings.USE_DATE_WIDGETS else {}),
            }
        ),
        label=gettext("Date of materials"),
        help_text=gettext(
            "Enter the range of dates that the materials cover, or a single date if there is "
            "no range."
        ),
    )

    date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
        label=gettext("Date is approximated"),
        help_text=gettext(
            "Check this box if the date is approximate, or if you are unsure of the date."
        ),
    )

    language_of_material = forms.CharField(
        required=True,
        min_length=2,
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": gettext("English, French")}),
        help_text=gettext("Enter all relevant languages here"),
        label=gettext("Language(s)"),
    )

    preliminary_scope_and_content = forms.CharField(
        required=True,
        min_length=4,
        max_length=2000,
        widget=forms.Textarea(
            attrs={"rows": "6", "placeholder": "e.g., These files contain images from ..."}
        ),
        label=gettext("Description of contents"),
        help_text=gettext(
            "Briefly describe the content of the files you are submitting. "
            "What do the files contain?"
        ),
    )

    condition_assessment = forms.CharField(
        required=False,
        min_length=4,
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": "6",
                "placeholder": "e.g., The documents are photocopies ... (optional)",
            }
        ),
        label=gettext("Condition of files"),
        help_text=gettext("Briefly describe the condition of the files you are submitting."),
    )


class ExtendedRecordDescriptionForm(RecordDescriptionForm):
    """Adds quantity and type of units to record description form. Intended to be used when file
    uploads are disabled.
    """

    quantity_and_unit_of_measure = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(
            attrs={
                "rows": "2",
                "placeholder": gettext(
                    "Record how many files and of what type they are that you "
                    "are planning on submitting (optional)"
                ),
            }
        ),
        help_text=gettext('For example, "200 PDF documents, totalling 2.0GB"'),
        label=gettext("Quantity and type of files"),
    )


class RightsFormSet(BaseFormSet):
    """Special formset to enforce at least one rights form to have a value."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.RIGHTS

    def __init__(self, *args, **kwargs):
        super(RightsFormSet, self).__init__(*args, **kwargs)
        self.forms[0].empty_permitted = False


class RightsForm(SubmissionForm):
    """The Rights portion of the form. Contains fields from Section 4 of CAAIS."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.RIGHTS

    def clean(self) -> dict:
        """Check that the rights type is set if the other rights type is not."""
        cleaned_data = super().clean()

        rights_type = cleaned_data.get("rights_type", None)
        other_rights_type = cleaned_data.get("other_rights_type", "")

        if rights_type and rights_type.name.lower() == "other" and not other_rights_type:
            self.add_error(
                "rights_type",
                gettext(
                    'If "Other type of rights" is empty, you must choose one of the '
                    "Rights types here"
                ),
            )
            self.add_error(
                "other_rights_type",
                gettext('If "Type of rights" is empty, you must enter a different type here'),
            )
        elif rights_type != RightsType.objects.get(name="Other"):
            cleaned_data["other_rights_type"] = ""  # Clear this field since it's not needed
            self.fields["other_rights_type"].label = "hidden"

        return cleaned_data

    rights_type = forms.ModelChoiceField(
        queryset=RightsType.objects.all()
        .annotate(
            sort_order_other_first=Case(
                When(name__iexact="other", then=Value("____")),
                default="name",
                output_field=CharField(),
            )
        )
        .order_by("sort_order_other_first"),
        label=gettext("Type of rights"),
        empty_label=gettext("Please select one"),
    )

    other_rights_type = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": gettext("Other type of rights not covered by other choices"),
                "class": "rights-select-other",
            }
        ),
        help_text=gettext('For example: "UK Human Rights Act 1998"'),
        label=gettext("Other type of rights"),
    )

    rights_value = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": "2",
                "placeholder": gettext(
                    "Any notes on these rights or which files they may apply to (optional)"
                ),
            }
        ),
        help_text=gettext('For example: "Copyright until 2050," "Only applies to images," etc.'),
        label=gettext("Notes for rights"),
    )

    # rights_note = forms.CharField(
    #     required=False,
    #     widget=forms.HiddenInput(),
    #     label='hidden'
    # )


class OtherIdentifiersForm(SubmissionForm):
    """The Other Identifiers portion of the form. Contains fields from Section 1 of CAAIS."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.OTHER_IDENTIFIERS

    def clean(self) -> dict:
        """Check that the other identifier type and value are set if the note is set."""
        cleaned_data = super().clean()

        id_type = cleaned_data.get("other_identifier_type")
        id_value = cleaned_data.get("other_identifier_value")
        id_note = cleaned_data.get("other_identifier_note")

        if id_type and not id_value:
            value_msg = "Must enter a value for this identifier"
            self.add_error("other_identifier_value", value_msg)
        elif not id_type and id_value:
            type_msg = "Must enter a type for this identifier"
            self.add_error("other_identifier_type", type_msg)
        elif not id_type and id_note:
            type_msg = "Must enter a type for this identifier"
            self.add_error("other_identifier_type", type_msg)
            value_msg = "Must enter a value for this identifier"
            self.add_error("other_identifier_value", value_msg)
            note_msg = "Cannot enter a note without entering a value and type"
            self.add_error("other_identifier_note", note_msg)
        return cleaned_data

    other_identifier_type = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": gettext("The type of the identifier"),
            }
        ),
        help_text=gettext('For example: "Receipt number", "LAC Record ID", etc.'),
        label=gettext("Type of identifier"),
    )

    other_identifier_value = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": gettext("Identifier value"),
            }
        ),
        label=gettext("Identifier value"),
    )

    other_identifier_note = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": "2",
                "placeholder": gettext(
                    "Any notes on this identifier or which files it may apply to (optional)."
                ),
            }
        ),
        label=gettext("Notes for identifier"),
    )


class OtherIdentifiersFormSet(BaseFormSet):
    """Special formset to add metadata to the other identifiers formset."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.OTHER_IDENTIFIERS


class GroupSubmissionForm(SubmissionForm):
    """Form for assigning a submission to a specific group."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.GROUP_SUBMISSION

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        user_submission_groups = SubmissionGroup.objects.filter(created_by=self.user)
        choices = [(None, "Select a group")] + [
            (group.uuid, group.name) for group in user_submission_groups
        ]
        self.fields["group_uuid"].choices = choices
        self.fields["group_uuid"].initial = None

    def clean(self) -> dict:
        """Check that chosen group exists and is owned by the user."""
        cleaned_data = super().clean()
        group_uuid = cleaned_data.get("group_uuid")

        if group_uuid:
            group = SubmissionGroup.objects.filter(created_by=self.user, uuid=group_uuid).first()
            cleaned_data["submission_group"] = group
            if not group:
                cleaned_data["group_uuid"] = None

        return cleaned_data

    group_uuid = forms.TypedChoiceField(
        required=False,
        coerce=UUID,
        widget=forms.Select(
            attrs={
                "class": "reduce-form-field-width",
                "id": HtmlIds.ID_SUBMISSION_GROUP_SELECTION,
            }
        ),
        label=gettext("Assigned group"),
    )


class UploadFilesForm(SubmissionForm):
    """The form where users upload their files and write any final notes."""

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.UPLOAD_FILES

    general_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(
            attrs={
                "rows": "6",
                "placeholder": gettext(
                    "Record any general notes you have about the records here (optional)"
                ),
            }
        ),
        help_text=gettext(
            "These should be notes that did not fit in any of the previous steps of this form"
        ),
        label=gettext("Other notes"),
    )

    session_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        label="hidden",
        error_messages={"required": "Upload session token is required"},
    )

    def clean(self) -> dict:
        """Check that the session token is valid and that at least one file has been uploaded."""
        cleaned_data = super().clean()
        session_token = cleaned_data.get("session_token")

        if not session_token:
            self.add_error("session_token", "Invalid upload. Please try again.")
            return cleaned_data

        try:
            upload_session = UploadSession.objects.get(token=session_token)
        except UploadSession.DoesNotExist:
            self.add_error("session_token", "Invalid upload. Please try again.")
            return cleaned_data

        if upload_session.file_count == 0:
            self.add_error("session_token", "You must upload at least one file")

        cleaned_data["quantity_and_unit_of_measure"] = (
            upload_session.get_quantity_and_unit_of_measure()
        )

        return cleaned_data


class FinalStepFormNoUpload(SubmissionForm):
    """The form where users write any final notes. Intended to be used in place of UploadFilesForm
    when file uploads are disabled.
    """

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.FINAL_NOTES

    general_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(
            attrs={
                "rows": "6",
                "placeholder": gettext(
                    "Record any general notes you have about the records here (optional)"
                ),
            }
        ),
        help_text=gettext(
            "These should be notes that did not fit in any of the previous steps of this form"
        ),
        label=gettext("Other notes"),
    )


class ReviewForm(SubmissionForm):
    """The final step of the form where the user can review their submission before sending
    it.
    """

    class Meta:
        """Meta information for the form."""

        submission_step = SubmissionStep.REVIEW

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible, label="hidden")

    @staticmethod
    def _get_base_fields_data(form: BaseForm) -> dict[str, Any]:
        """Extract fields data from a form."""
        return {
            form.fields[field].label or field: form.cleaned_data.get(field, "")
            for field in form.fields
            if form.fields[field].label != "hidden"
        }

    @staticmethod
    def _get_file_upload_fields_data(form: UploadFilesForm, user: User) -> dict[str, Any]:
        """Handle file upload specific field processing."""
        fields_data = ReviewForm._get_base_fields_data(form)
        session_token = form.cleaned_data.get("session_token")

        if not (session_token and user):
            return fields_data

        session = UploadSession.objects.filter(token=session_token, user=user).first()
        if not session:
            return fields_data

        # Adds on links to access uploaded files
        fields_data["Uploaded files"] = [
            {"name": f.name, "url": f.get_file_access_url()}
            for f in session.get_temporary_uploads()
        ]

        return fields_data

    @staticmethod
    def _get_group_submission_fields_data(form: GroupSubmissionForm, user: User) -> dict[str, Any]:
        """Handle group submission specific field processing."""
        fields_data = ReviewForm._get_base_fields_data(form)
        group_uuid = form.cleaned_data.get("group_uuid")

        if not (group_uuid and user):
            return fields_data

        group = SubmissionGroup.objects.filter(created_by=user, uuid=group_uuid).first()
        if not group:
            return fields_data

        # Replaces group UUID with group name
        group_uuid_label = form.fields["group_uuid"].label
        if group_uuid_label:
            fields_data[group_uuid_label] = group.name

        return fields_data

    @staticmethod
    def _get_formset_fields_data(form: BaseFormSet) -> tuple[list[dict[str, Any]], Optional[str]]:
        """Process a formset and return formatted data with optional note."""
        formset_data = []
        note = None
        all_empty = True

        for subform in form.forms:
            subform_data = {
                subform.fields[field].label or field: subform.cleaned_data.get(field, "")
                for field in subform.fields
                if subform.fields[field].label != "hidden"
            }

            if any(subform_data.values()):
                all_empty = False
                formset_data.append(subform_data)

        if all_empty and isinstance(form, OtherIdentifiersFormSet):
            note = gettext("No other identifiers were provided.")

        return formset_data, note

    @staticmethod
    def format_form_data(
        form_dict: OrderedDict[str, Union[BaseForm, BaseFormSet]], user: User
    ) -> list[ReviewFormItem]:
        """Format form data to be used in a form review page."""
        preview_data: list[ReviewFormItem] = []

        for step_title, form in form_dict.items():
            # Each form has metadata that links it to a step in the submission form
            meta = getattr(form.__class__, "Meta", None)
            submission_step = meta.submission_step if meta else None

            if isinstance(form, BaseFormSet):  # Handle formsets
                formset_data, note = ReviewForm._get_formset_fields_data(form)
                preview_data.append(
                    {
                        "step_title": step_title,
                        "step_name": submission_step.value if submission_step else "",
                        "fields": formset_data,
                        "note": note,  # A note is included if the formset is empty
                    }
                )

            elif isinstance(form, BaseForm):  # Handle regular forms
                if isinstance(form, GroupSubmissionForm):
                    fields_data = ReviewForm._get_group_submission_fields_data(form, user)
                elif isinstance(form, UploadFilesForm):
                    fields_data = ReviewForm._get_file_upload_fields_data(form, user)
                else:
                    fields_data = ReviewForm._get_base_fields_data(form)

                preview_data.append(
                    {
                        "step_title": step_title,
                        "step_name": submission_step.value if submission_step else "",
                        "fields": fields_data,
                        "note": None,
                    }
                )

        return preview_data


def clear_form_errors(form: Union[BaseForm, BaseFormSet]) -> None:
    """Clear all errors on a form or formset."""
    if isinstance(form, BaseForm):
        form.errors.clear()
        for field in form.fields:
            form.fields[field].error_messages.clear()
    elif isinstance(form, BaseFormSet):
        for subform in form.forms:
            subform.errors.clear()
            for field in subform.fields:
                subform.fields[field].error_messages.clear()
