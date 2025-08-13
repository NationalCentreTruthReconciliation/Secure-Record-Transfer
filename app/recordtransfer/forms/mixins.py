from django import forms
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox, ReCaptchaV2Invisible

from recordtransfer.constants import HtmlIds, OtherValues
from recordtransfer.widgets import CustomCountrySelectWidget


class ContactInfoFormMixin(forms.Form):
    """Mixin containing address-related form fields."""

    phone_number = forms.RegexField(
        regex=r"^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$",
        error_messages={
            "required": _("This field is required."),
            "invalid": _('Phone number must look like "+1 (999) 999-9999"'),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "+1 (999) 999-9999",
            }
        ),
        label=_("Phone number"),
    )

    address_line_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Street, and street number")}),
        label=_("Address line 1"),
    )

    address_line_2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Unit Number, RPO, PO BOX... (optional)")}),
        label=_("Address line 2"),
    )

    city = forms.CharField(
        max_length=100,
        required=True,
        label=_("City"),
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
            ("", _("Select your province")),
            # Canada
            ("AB", "Alberta"),
            ("BC", "British Columbia"),
            ("MB", "Manitoba"),
            ("NB", "New Brunswick"),
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
            ("AK", "Alaska"),
            ("AZ", "Arizona"),
            ("AR", "Arkansas"),
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
            # Other values
            ("Other", _(OtherValues.PROVINCE_OR_STATE)),
        ],
        initial="",
        label=_("Province or state"),
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
        label=_("Other province or state"),
    )

    postal_or_zip_code = forms.RegexField(
        regex=r"^(?:[0-9]{5}(?:-[0-9]{4})?)|(?:[A-Za-z]\d[A-Za-z][\- ]?\d[A-Za-z]\d)$",
        error_messages={
            "required": _("This field is required."),
            "invalid": _(
                'Postal code must look like "Z0Z 0Z0", zip code must look like '
                '"12345" or "12345-1234"'
            ),
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Z0Z 0Z0",
            }
        ),
        label=_("Postal / Zip code"),
    )

    country = CountryField(blank_label=_("Select your Country")).formfield(
        widget=CustomCountrySelectWidget(
            attrs={
                "class": "reduce-form-field-width",
            }
        ),
        label=_("Country"),
    )

    def clean_address_fields(self) -> dict:
        """Ensure that the province_or_state field is filled out if 'Other' is selected."""
        cleaned_data = self.cleaned_data or {}
        region = cleaned_data.get("province_or_state", "").lower()
        other_region = cleaned_data.get("other_province_or_state", "")
        address_line_1 = cleaned_data.get("address_line_1", "").strip()
        address_line_2 = cleaned_data.get("address_line_2", "").strip()

        if address_line_2 and not address_line_1:
            self.add_error(
                "address_line_1",
                _("Address line 1 is required if address line 2 is provided."),
            )

        if not region:
            self.add_error(
                "province_or_state",
                'You must select a province or state, use "Other" to enter a custom location',
            )
        elif region == "other":
            if not other_region:
                self.add_error(
                    "other_province_or_state",
                    'This field must be filled out if "Other" province or state is selected',
                )
        else:
            cleaned_data["other_province_or_state"] = ""
            self.fields["other_province_or_state"].label = "hidden"

        return cleaned_data


class HiddenCaptchaMixin:
    """Add to forms that require reCAPTCHA validation."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible, label="hidden")


class VisibleCaptchaMixin:
    """Add to forms that require visible reCAPTCHA validation."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox, label=_("Please verify you are human"))
