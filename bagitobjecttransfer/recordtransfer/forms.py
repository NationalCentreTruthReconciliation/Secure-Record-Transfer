from datetime import datetime

from django import forms
from django_countries.fields import CountryField

from recordtransfer.validators import validate_date, FULL_DATE, SINGLE_YEAR


class SourceInfoForm(forms.Form):
    source_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'The organization or entity submitting the records'
        }),
    )

    source_type = forms.CharField(
        max_length=64,
        min_length=2,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'The kind of entity the source is (optional)'
        }),
    )

    source_role = forms.ChoiceField(
        required=True,
        choices=[
            (c, c) for c in [
                'Creator',
                'Donor',
                'Custodian',
                'Unknown',
            ]
        ],
        widget=forms.Select,
    )

    source_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': 'Enter any notes you have on how the source relates to the records'
                           ' (optional)'
        }),
    )

    custodial_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': 'Enter any notes you have on how the custodial history of the records'
                           ' (optional)'
        }),
    )


class ContactInfoForm(forms.Form):
    contact_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your name'
        }),
    )

    job_title = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your job title'
        }),
    )

    phone_number = forms.RegexField(
        regex=r'^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$',
        error_messages={
            'required': 'This field is required.',
            'invalid': 'Phone number must look like "+1 (999) 999-9999"'
        },
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (999) 999-9999'
        }),
        help_text='Phone number should look like "+1 (123) 456-7890"'
    )

    email = forms.EmailField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your email'
        }),
    )

    address_line_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Street, and street number'
        }),
    )

    address_line_2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Unit Number, RPO, PO BOX... (optional)'
        }),
    )

    province_or_state = forms.ChoiceField(
        required=True,
        choices=[
            (c, c) for c in [
                # For non-Canadian or non-US addresses
                "Other",
                # Canadian Provinces
                "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC",
                "SK", "YT",
                # US States
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
                "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
                "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
                "UT", "VT", "VA", "WA", "WV", "WI", "WY"
            ]
        ],
        widget=forms.Select
    )

    postal_or_zip_code = forms.CharField(
        min_length=4
    )

    country = CountryField(blank_label='Select your Country').formfield()


class RecordDescriptionForm(forms.Form):
    def get_year_month_day(self, value):
        year_match = SINGLE_YEAR.match(value)
        if year_match:
            year = int(year_match.group('year'))
            month = date = 0
        else:
            full_match = FULL_DATE.match(value)
            year = int(full_match.group('year'))
            month = int(full_match.group('month'))
            date = int(full_match.group('date'))
        return (year, month, date)

    def clean(self):
        cleaned_data = super().clean()

        start_date_of_material = cleaned_data.get('start_date_of_material')
        end_date_of_material = cleaned_data.get('end_date_of_material')

        # Check end date after start date
        if start_date_of_material and end_date_of_material:
            start_year_only = False
            start_year, start_month, start_date = self.get_year_month_day(start_date_of_material)
            if start_month == 0 or start_date == 0:
                start_year_only = True

            end_year_only = False
            end_year, end_month, end_date = self.get_year_month_day(end_date_of_material)
            if end_month == 0 or end_date == 0:
                end_year_only = True

            # Fix zero-ed months and dates
            if start_year_only and end_year_only:
                start_month = start_date = end_month = end_date = 1
            elif start_year_only and not end_year_only:
                start_month, start_date = end_month, end_date
            elif not start_year_only and end_year_only:
                end_month, end_date = start_month, start_date

            start_datetime = datetime(start_year, start_month, start_date)
            end_datetime = datetime(end_year, end_month, end_date)

            if end_datetime == start_datetime:
                msg = 'Start and end dates are equivalent. Change one of them'
                self.add_error('start_date_of_material', msg)
                self.add_error('end_date_of_material', msg)
            elif end_datetime < start_datetime:
                msg = 'End date cannot be before start date'
                self.add_error('end_date_of_material', msg)


    collection_title = forms.CharField(
        min_length=2,
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Create a title for this collection of records'
        }),
    )

    start_date_of_material = forms.RegexField(
        # Date regex is a little lax, but this is on purpose since I want the more verbose errors
        # that the validate_date validator sends back.
        regex=r'^(?:\d{4})|(?:\d{4})-(?:\d{2})-(?:\d{2})$',
        required=True,
        error_messages={
            'required': 'This field is required.',
        },
        widget=forms.TextInput(attrs={
            'placeholder': '2000-01-01'
        }),
        validators=[validate_date],
        help_text='Enter either a single year or a yyyy-mm-dd formatted date'
    )

    start_date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
        help_text='Check the box if the start date is an estimate or a guess'
    )

    end_date_of_material = forms.RegexField(
        regex=r'^(?:\d{4})|(?:\d{4})-(?:\d{2})-(?:\d{2})$',
        required=True,
        error_messages={
            'required': 'This field is required.',
        },
        widget=forms.TextInput(attrs={
            'placeholder': '2000-12-31'
        }),
        validators=[validate_date],
        help_text='Enter either a single year or a yyyy-mm-dd formatted date'
    )

    end_date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
        help_text='Check the box if the end date is an estimate or a guess'
    )

    language_of_material = forms.CharField(
        required=True,
        min_length=2,
        widget=forms.TextInput(attrs={
            'placeholder': 'English, French'
        }),
        help_text='Enter all relevant languages here'
    )

    description = forms.CharField(
        required=True,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': 'Briefly describe the scope and content of the files to be transferred'
        }),
    )


class RightsForm(forms.Form):
    rights_type = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter the type of rights govern the records',
        }),
        help_text='e.g., Copyright, cultural rights, etc. If public domain, put Copyright.',
    )

    rights_statement = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nature and duration of permission or restrictions',
        }),
        help_text='e.g., Public domain, Records subject to Province of Manitoba\'s FIPPA, etc.',
    )

    rights_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': 'Any notes on these rights (optional).',
        }),
    )


class OtherIdentifiersForm(forms.Form):
    other_identifier_type = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'The kind of identifier',
        }),
        help_text='e.g., may be a receipt number, an ID from another records system, etc.',
    )

    identifier_value = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Identifier value',
        }),
    )

    identifier_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': 'Any notes on this identifier (optional).',
        }),
    )


class UploadFilesForm(forms.Form):
    session_token = forms.CharField(widget=forms.HiddenInput())
