from django import forms
from django.utils.translation import gettext
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from recordtransfer.constants import HtmlIds, OtherValues


class ContactInfoMixin(forms.Form):
    """Mixin containing address-related form fields."""

    def __init__(self, *args, **kwargs):
        if not isinstance(self, forms.BaseForm):
            raise TypeError(
                f"{self.__class__.__name__} must inherit from a Django Form class "
                f"(forms.Form, forms.ModelForm, etc.) when using AddressMixin"
            )
        super().__init__(*args, **kwargs)

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

    def clean_address_fields(self) -> dict:
        """Ensure that the province_or_state field is filled out if 'Other'
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
            cleaned_data["other_province_or_state"] = ""
            self.fields["other_province_or_state"].label = "hidden"
        return cleaned_data
