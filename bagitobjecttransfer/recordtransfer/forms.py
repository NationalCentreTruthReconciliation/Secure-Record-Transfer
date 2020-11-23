''' These are the forms that users will fill to transfer records to your institution. Each of these
are based on the CAAIS fields, but have been rearranged to fit a more natural form entry experience.

The form is split into multiple related pieces. The reason a single form is not used is because it
would be too long, and might create a negative experience, especially on mobile.

Remember that each form must be specified in the wizard in :code:`urls.py`.
'''
import json
from collections import OrderedDict

from django import forms
from django.utils import timezone
from django.utils.translation import gettext
from django.contrib.auth.forms import UserCreationForm

from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from recordtransfer.models import User, Bag
from recordtransfer.settings import DEFAULT_DATA


class BagForm(forms.ModelForm):
    ''' Form used to edit a Bag in the admin '''

    class Meta:
        model = Bag
        fields = (
            'bagging_date',
            'bag_name',
            'caais_metadata',
            'user',
            'review_status',
        )

    disabled_fields = ['bagging_date', 'bag_name', 'caais_metadata', 'user']

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Disable fields
            for field in self.disabled_fields:
                self.fields[field].disabled = True
            self.fields['caais_metadata'].help_text = gettext('Click View Metadata as HTML below '
                                                              'for a human-readable report')
            # Load string metadata as object
            self._bag_metadata = json.loads(instance.caais_metadata)

            accession_id = self._bag_metadata['section_1']['accession_identifier']
            self.fields['accession_identifier'].initial = accession_id
            level_of_detail = self._bag_metadata['section_7']['level_of_detail']
            self.fields['level_of_detail'].initial = level_of_detail or 'Not Specified'

    def clean(self):
        cleaned_data = super().clean()
        caais_metadata_changed = False

        new_accession_id = cleaned_data['accession_identifier']
        curr_accession_id = self._bag_metadata['section_1']['accession_identifier']
        if curr_accession_id != new_accession_id and new_accession_id:
            if not curr_accession_id or \
                (curr_accession_id == DEFAULT_DATA['section_1'].get('accession_identifier')):
                note = f'Accession ID was set to "{new_accession_id}"'
                self.log_new_event('Accession ID Assigned', note)
            else:
                note = f'Accession ID Changed from "{curr_accession_id}" to "{new_accession_id}"'
                self.log_new_event('Accession ID Modified', note)
            self._bag_metadata['section_1']['accession_identifier'] = new_accession_id
            caais_metadata_changed = True

        appraisal_value = cleaned_data['appraisal_statement_value']
        if appraisal_value:
            appraisal = OrderedDict()
            appraisal_type = cleaned_data['appraisal_statement_type']
            appraisal_note = cleaned_data['appraisal_statement_note']
            appraisal['appraisal_statement_type'] = appraisal_type
            appraisal['appraisal_statement_value'] = appraisal_value
            appraisal['appraisal_statement_note'] = appraisal_note
            self.log_new_event(f'{appraisal_type} Added')
            self._bag_metadata['section_4']['appraisal_statement'].append(appraisal)
            caais_metadata_changed = True

        level_of_detail = cleaned_data['level_of_detail']
        curr_level_of_detail = self._bag_metadata['section_7']['level_of_detail']
        if curr_level_of_detail != level_of_detail and level_of_detail and \
            level_of_detail != 'Not Specified':
            if not curr_level_of_detail or \
                (curr_level_of_detail == DEFAULT_DATA['section_7'].get('level_of_detail')):
                note = f'Level of Detail was set to {level_of_detail}'
                self.log_new_event('Level of Detail Assigned', note)
            else:
                note = f'Level of Detail Changed from {curr_level_of_detail} to {level_of_detail}'
                self.log_new_event('Level of Detail Changed', note)
            self._bag_metadata['section_7']['level_of_detail'] = level_of_detail
            caais_metadata_changed = True

        if caais_metadata_changed:
            cleaned_data['caais_metadata'] = json.dumps(self._bag_metadata)

        return cleaned_data

    def log_new_event(self, event_type: str, event_note: str = ''):
        new_event = OrderedDict()
        new_event['event_type'] = event_type
        new_event['event_date'] = timezone.now().strftime(r'%Y-%m-%d %H:%M:%S %Z')
        if self.current_user:
            new_event['event_agent'] = (f'User {self.current_user.username} '
                                        f'({self.current_user.email})')
        else:
            new_event['event_agent'] = 'Transfer Portal User'
        new_event['event_note'] = event_note
        self._bag_metadata['section_5']['event_statement'].append(new_event)

    accession_identifier = forms.CharField(
        max_length=128,
        min_length=2,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Update Accession ID')
        }),
        label=gettext('Accession identifier'),
        help_text=gettext('Saving any change to this field will log a new event in the Caais '
                          'metadata'),
    )

    level_of_detail = forms.ChoiceField(
        choices = [(c, c) for c in [
            'Not Specified',
            'Minimal',
            'Partial',
            'Full',
        ]],
        required=False,
        widget=forms.Select(),
        label=gettext('Level of detail'),
        help_text=gettext('Saving any change to this field will log a new event in the Caais '
                          'metadata'),
    )

    appraisal_statement_type = forms.ChoiceField(
        choices = [(c, c) for c in [
            'Archival Appraisal',
            'Monetary Appraisal',
        ]],
        required=False,
        widget=forms.Select(),
        label=gettext('New Appraisal Type'),
    )

    appraisal_statement_value = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Record a new appraisal statement here.'),
        }),
        label=gettext('New Appraisal Statement'),
        help_text=gettext('Leave empty if you do not want to add an appraisal statement'),
    )

    appraisal_statement_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Record any notes about the appraisal statement here '
                                   '(optional).'),
        }),
        label=gettext('Notes About Appraisal Statement'),
        help_text=gettext('Leave empty if you do not want to add an appraisal statement'),
    )


class SignUpForm(UserCreationForm):
    ''' Form for a user to create a new account '''

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean(self):
        ''' Clean data, make sure username and email are not already in use. '''
        cleaned_data = super().clean()
        new_username = cleaned_data['username']
        username_exists = User.objects.filter(username=new_username).first() is not None
        if username_exists:
            self.add_error('username', f'The username {new_username} is already in use')
        new_email = cleaned_data['email']
        email_exists = User.objects.filter(email=new_email).first() is not None
        if email_exists:
            self.add_error('email', f'The email {new_email} is already in use')

    email = forms.EmailField(max_length=256,
        required=True,
        widget=forms.TextInput(),
        label=gettext('Email'))

    username = forms.CharField(max_length=256,
        min_length=6,
        required=True,
        widget=forms.TextInput(),
        label=gettext('Username'),
        help_text=gettext('This is the username you will use to log in to your account'))

    first_name = forms.CharField(max_length=256,
        min_length=2,
        required=True,
        widget=forms.TextInput(),
        label=gettext('First name'))

    last_name = forms.CharField(max_length=256,
        min_length=2,
        required=True,
        widget=forms.TextInput(),
        label=gettext('Last name'))


class ContactInfoForm(forms.Form):
    ''' The Contact Information portion of the form. Contains fields from Section 2 of CAAIS '''
    contact_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        label=gettext('Contact name'),
    )

    job_title = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        label=gettext('Job title'),
    )

    phone_number = forms.RegexField(
        regex=r'^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$',
        error_messages={
            'required': gettext('This field is required.'),
            'invalid': gettext('Phone number must look like "+1 (999) 999-9999"')
        },
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (999) 999-9999',
            'class': 'reduce-form-field-width',
        }),
        help_text=gettext('Phone number should look like "+1 (123) 456-7890"'),
        label=gettext('Phone number'),
    )

    email = forms.EmailField(
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

    city = forms.CharField(
        max_length=100,
        required=True,
        label=gettext('City'),
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
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
    )

    postal_or_zip_code = forms.RegexField(
        regex=r'^(?:[0-9]{5}(?:-[0-9]{4})?)|(?:[A-Za-z]\d[A-Za-z][\- ]?\d[A-Za-z]\d)$',
        error_messages={
            'required': gettext('This field is required.'),
            'invalid': gettext('Postal code must look like "Z0Z 0Z0", zip code must look like '
                               '"12345" or "12345-1234"')
        },
        widget=forms.TextInput(attrs={
            'placeholder': 'Z0Z 0Z0',
            'class': 'reduce-form-field-width',
        }),
        label=gettext('Postal / Zip code'),
    )

    country = CountryField(blank_label=gettext('Select your Country')).formfield(
        widget=CountrySelectWidget(
            attrs={
                'class': 'reduce-form-field-width',
            }
        )
    )


class SourceInfoForm(forms.Form):
    ''' The Source Information portion of the form. Contains fields from Section 2 of CAAIS '''
    source_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('The organization or entity submitting the records')
        }),
        label=gettext('Name of source'),
    )

    source_type = forms.ChoiceField(
        required=True,
        choices=[
            (c, c) for c in [
                gettext('Person'),
                gettext('Family'),
                gettext('Band'),
                gettext('Company'),
                gettext('Corporation'),
                gettext('Organization'),
                gettext('Educational Institution'),
                gettext('Government Office'),
                gettext('Other'),
                gettext('Unknown'),
            ]
        ],
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
        label=gettext('The source is a(n)'),
        help_text=gettext('How would you describe <b>what</b> the source entity is?'),
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
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
        label=gettext('The source\'s relationship to the records'),
        help_text=gettext('How would you describe <b>how</b> the source relates to the records?'),
    )

    source_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': gettext('Enter any notes you think may be useful for the archives to '
                                   'have about this entity (optional)')
        }),
        label=gettext('Source notes'),
        help_text=gettext('e.g., The donor wishes to remain anonymous')
    )

    custodial_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': gettext('Enter any information you have on the history of who has had '
                                   'custody of the records or who has kept the records in the past '
                                   '(optional)')
        }),
        label=gettext('Custodial history'),
        help_text=gettext('e.g., John Doe held these records before donating them in 1960'),
    )


class RecordDescriptionForm(forms.Form):
    ''' The Description Information portion of the form. Contains fields from Section 3 of CAAIS '''
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
            'class': 'start_date_picker reduce-form-field-width',
            'autocomplete': 'off',
            'placeholder': 'yyyy-mm-dd',
        }),
        label=gettext('Earliest date of files'),
        help_text=gettext('Enter the earliest date relevant to the files you\'re transferring.'),
    )

    start_date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'hidden': True,
        }),
        label='hidden',
    )

    end_date_of_material = forms.DateField(
        input_formats=[r'%Y-%m-%d'],
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'end_date_picker reduce-form-field-width',
            'autocomplete': 'off',
            'placeholder': 'yyyy-mm-dd',
        }),
        label=gettext('Latest date of files'),
        help_text=gettext('Enter the latest date relevant to the files you\'re transferring.'),
    )

    end_date_is_approximate = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'hidden': True,
        }),
        label='hidden',
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
            'placeholder': gettext('Briefly describe the content of the files you are '
                                   'transferring. What do the files contain?')
        }),
        label=gettext('Description of files'),
    )


class RightsForm(forms.Form):
    ''' The Rights portion of the form. Contains fields from Section 4 of CAAIS '''
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
    ''' The Other Identifiers portion of the form. Contains fields from Section 1 of CAAIS '''
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


class GeneralNotesForm(forms.Form):
    ''' The Other Identifiers portion of the form. Contains fields from Section 6 of CAAIS '''
    general_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Record any general notes you have about the records here '
                                   '(optional)')
        }),
        help_text=gettext('These should be notes that did not fit in any of the previous steps of '
                          'this form'),
        label=gettext('Other notes'),
    )


class UploadFilesForm(forms.Form):
    ''' The form where users upload their files '''
    session_token = forms.CharField(widget=forms.HiddenInput())
