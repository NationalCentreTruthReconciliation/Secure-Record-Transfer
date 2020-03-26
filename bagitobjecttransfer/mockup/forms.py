from datetime import datetime

from django import forms
from django_countries.fields import CountryField

from mockup.validators import validate_date, FULL_DATE, SINGLE_YEAR


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
    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date_of_material')
        end_date = cleaned_data.get('end_date_of_material')

        # Check end date after start date
        if start_date and end_date:
            start_year_only = False
            start_date_year_match = SINGLE_YEAR.match(start_date)
            if start_date_year_match:
                start_year_only = True
                start_year = int(start_date_year_match.group('year'))
                start_month = 0
                start_date = 0
            else:
                start_date_full_match = FULL_DATE.match(start_date)
                start_year = int(start_date_full_match.group('year'))
                start_month = int(start_date_full_match.group('month'))
                start_date = int(start_date_full_match.group('date'))

            end_year_only = False
            end_date_year_match = SINGLE_YEAR.match(end_date)
            if end_date_year_match:
                end_year_only = True
                end_year = int(end_date_year_match)
                end_month = 0
                end_date = 0
            else:
                end_date_full_match = FULL_DATE.match(end_date)
                end_year = int(end_date_full_match.group('year'))
                end_month = int(end_date_full_match.group('month'))
                end_date = int(end_date_full_match.group('date'))

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


class UploadFilesForm(forms.Form):
    session_token = forms.CharField(widget=forms.HiddenInput())
