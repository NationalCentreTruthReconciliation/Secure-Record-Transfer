from django import forms
from django_countries.fields import CountryField
from django.utils.translation import gettext


class SourceInfoForm(forms.Form):
    source_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('The organization or entity submitting the records')
        }),
        label=gettext('Source name'),
    )

    source_type = forms.CharField(
        max_length=64,
        min_length=2,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('The kind of entity the source is (optional)')
        }),
        label=gettext('Source type'),
        help_text=gettext('For example: Individual, Company, Corporation, etc.'),
    )

    source_role = forms.ChoiceField(
        required=True,
        choices=[
            (c, c) for c in [
                gettext('Creator'),
                gettext('Donor'),
                gettext('Custodian'),
                gettext('Other'),
                gettext('Unknown'),
            ]
        ],
        widget=forms.Select,
        label=gettext('Source role'),
    )

    source_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': gettext('Enter any notes you have on how the source relates to the '
                                   'records (optional)')
        }),
        label=gettext('Source note'),
    )

    custodial_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': gettext('Enter any notes you have on the custodial history of the '
                                   'records (optional)')
        }),
    )


class ContactInfoForm(forms.Form):
    contact_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Enter your name')
        }),
        label=gettext('Contact name'),
    )

    job_title = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Enter your job title')
        }),
        label=gettext('Job title'),
    )

    phone_number = forms.RegexField(
        regex=r'^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$',
        error_messages={
            'required': gettext('This field is required.'),
            'invalid': gettext('Phone number must look like "+1 (999) 999-9999"')
        },
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (999) 999-9999'
        }),
        help_text=gettext('Phone number should look like "+1 (123) 456-7890"'),
        label=gettext('Phone number'),
    )

    email = forms.EmailField(
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Enter your email')
        }),
        label=gettext('Email'),
    )

    address_line_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Street, and street number')
        }),
        label=gettext('Address line 1'),
    )

    address_line_2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Unit Number, RPO, PO BOX... (optional)')
        }),
        label=gettext('Address line 2'),
    )

    province_or_state = forms.ChoiceField(
        required=True,
        choices=[
            (c, c) for c in [
                # For non-Canadian or non-US addresses
                gettext("Other"),
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
        widget=forms.Select,
    )

    postal_or_zip_code = forms.RegexField(
        regex=r'^(?:[0-9]{5}(?:-[0-9]{4})?)|(?:[A-Za-z]\d[A-Za-z][\- ]?\d[A-Za-z]\d)$',
        error_messages={
            'required': gettext('This field is required.'),
            'invalid': gettext('Postal code must look like "Z0Z 0Z0", zip code must look like '
                               '"12345" or "12345-1234"')
        },
        widget=forms.TextInput(attrs={
            'placeholder': 'Z0Z 0Z0'
        }),
        label=gettext('Postal / Zip code'),
    )

    country = CountryField(blank_label=gettext('Select your Country')).formfield()


class RecordDescriptionForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()

        start_date_of_material = cleaned_data.get('start_date_of_material')
        end_date_of_material = cleaned_data.get('end_date_of_material')
        if not start_date_of_material:
            self.add_error('start_date_of_material', 'Start date was not valid')
        if not end_date_of_material:
            self.add_error('end_date_of_material', 'End date was not valid')
        if start_date_of_material and end_date_of_material:
            if end_date_of_material < start_date_of_material:
                msg = 'End date cannot be before start date'
                self.add_error('end_date_of_material', msg)

    accession_title = forms.CharField(
        min_length=2,
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Create a title for this collection of records')
        }),
        label=gettext('Collection title')
    )

    start_date_of_material = forms.DateField(
        input_formats=[r'%Y-%m-%d'],
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'start_date_picker',
            'autocomplete': 'off',
        }),
        label=gettext('Start date of material'),
    )

    start_date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
        help_text=gettext('Check the box if the start date is an estimate or a guess'),
        label=gettext('Start date estimated'),
    )

    end_date_of_material = forms.DateField(
        input_formats=[r'%Y-%m-%d'],
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'end_date_picker',
            'autocomplete': 'off',
        }),
        label=gettext('End date of files'),
    )

    end_date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
        help_text=gettext('Check the box if the end date is an estimate or a guess'),
        label=gettext('End date estimated'),
    )

    language_of_material = forms.CharField(
        required=True,
        min_length=2,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('English, French')
        }),
        help_text=gettext('Enter all relevant languages here'),
        label=gettext('Language of material')
    )

    scope_and_content = forms.CharField(
        required=True,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Briefly describe the content of the files you are transferring')
        }),
        label=gettext('Description'),
    )


class RightsForm(forms.Form):
    rights_statement_type = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Enter the type of rights governing the records'),
            'required': 'required',
        }),
        help_text=gettext('For example: "Copyright," "Cultural rights," etc.'),
        label=gettext('Type of rights'),
    )

    rights_statement_value = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Nature and duration of permission or restrictions'),
            'required': 'required',
        }),
        help_text=gettext('For example: "Public domain," "FIPPA," "Copyright until 2050," etc.'),
        label=gettext('Description of rights'),
    )

    rights_statement_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': gettext('Any notes on these rights or which files they may apply to '
                                   '(optional).'),
        }),
        label=gettext('Notes for rights')
    )


class OtherIdentifiersForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()

        id_type = cleaned_data.get('other_identifier_type')
        id_value = cleaned_data.get('other_identifier_value')
        id_note = cleaned_data.get('other_identifier_note')

        if id_type and not id_value:
            value_msg = 'Must enter a value for this identifier'
            self.add_error('other_identifier_value', value_msg)
        elif not id_type and id_value:
            type_msg = 'Must enter a type for this identifier'
            self.add_error('other_identifier_type', type_msg)
        elif not id_type and id_note:
            type_msg = 'Must enter a type for this identifier'
            self.add_error('other_identifier_type', type_msg)
            value_msg = 'Must enter a value for this identifier'
            self.add_error('other_identifier_value', value_msg)
            note_msg = 'Cannot enter a note without entering a value and type'
            self.add_error('other_identifier_note', note_msg)

    other_identifier_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('The type of the identifier'),
        }),
        help_text=gettext('For example: "Receipt number", "LAC Record ID", etc.'),
        label=gettext('Type of identifier'),
    )

    other_identifier_value = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Identifier value'),
        }),
        label=gettext('Identifier value'),
    )

    other_identifier_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': gettext('Any notes on this identifier or which files it may apply to '
                                   '(optional).')
        }),
        label=gettext('Notes for identifier')
    )


class UploadFilesForm(forms.Form):
    session_token = forms.CharField(widget=forms.HiddenInput())

    general_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Put any other notes you would like to add for this transfer '
                                   'here (optional)')
        }),
        label=gettext('Other notes'),
    )
