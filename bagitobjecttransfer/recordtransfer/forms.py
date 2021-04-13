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


class InlineBagForm(forms.ModelForm):
    ''' Form used to view inline Bag '''
    class Meta:
        model = Bag
        fields = (
            'bagging_date',
            'bag_name',
            'user',
            'review_status',
        )
    disabled_fields = ['bagging_date', 'bag_name', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Disable fields
            for field in self.disabled_fields:
                self.fields[field].disabled = True


class BagForm(forms.ModelForm):
    ''' Form used to edit a Bag in the admin '''

    class Meta:
        model = Bag
        fields = (
            'bagging_date',
            'bag_name',
            'caais_metadata',
            'user',
            'part_of_group',
            'review_status',
        )

    disabled_fields = ['bagging_date', 'bag_name', 'caais_metadata', 'user', 'part_of_group']


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
        return cleaned_data

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


class AcceptLegal(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['agreement_accepted']:
            self.add_error('agreement_accepted', 'You must accept before continuing')

    agreement_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(),
        label=gettext('I accept these terms'),
    )


class ContactInfoForm(forms.Form):
    ''' The Contact Information portion of the form. Contains fields from Section 2 of CAAIS '''
    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data['province_or_state']
        if region.lower() == 'other' and not cleaned_data['other_province_or_state']:
            self.add_error('other_province_or_state',
                           'This field must be filled out if "Other" province or state is selected')
        return cleaned_data

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
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
        choices=[
            # Canada
            ('Other', gettext("Other")),
            ('AB', 'Alberta'),
            ('BC', 'British Columbia'),
            ('MB', 'Manitoba'),
            ('NL', 'Newfoundland and Labrador'),
            ('NT', 'Northwest Territories'),
            ('NS', 'Nova Scotia'),
            ('NU', 'Nunavut'),
            ('ON', 'Ontario'),
            ('PE', 'Prince Edward Island'),
            ('QC', 'Quebec'),
            ('SK', 'Saskatchewan'),
            ('YT', 'Yukon Territory'),
            # United States of America
            ('AL', 'Alabama'),
            ('AK', 'Arkansas'),
            ('AZ', 'Arizona'),
            ('AR', 'Arkanasas'),
            ('CA', 'California'),
            ('CO', 'Colorado'),
            ('CT', 'Connecticut'),
            ('DE', 'Delaware'),
            ('DC', 'District of Columbia'),
            ('FL', 'Florida'),
            ('GA', 'Georgia'),
            ('HI', 'Hawaii'),
            ('ID', 'Idaho'),
            ('IL', 'Illinois'),
            ('IN', 'Indiana'),
            ('IA', 'Iowa'),
            ('KS', 'Kansas'),
            ('KY', 'Kentucky'),
            ('LA', 'Louisiana'),
            ('ME', 'Maine'),
            ('MD', 'Maryland'),
            ('MA', 'Massachusetts'),
            ('MI', 'Michigan'),
            ('MN', 'Minnesota'),
            ('MS', 'Mississippi'),
            ('MO', 'Missouri'),
            ('MT', 'Montana'),
            ('NE', 'Nebraska'),
            ('NV', 'Nevada'),
            ('NH', 'New Hampshire'),
            ('NJ', 'New Jersey'),
            ('NM', 'New Mexico'),
            ('NY', 'New York'),
            ('NC', 'North Carolina'),
            ('ND', 'North Dakota'),
            ('OH', 'Ohio'),
            ('OK', 'Oklahoma'),
            ('OR', 'Oregon'),
            ('PA', 'Pennsylvania'),
            ('RI', 'Rhode Island'),
            ('SC', 'South Carolina'),
            ('SD', 'South Dakota'),
            ('TN', 'Tennessee'),
            ('TX', 'Texas'),
            ('UT', 'Utah'),
            ('VT', 'Vermont'),
            ('VA', 'Virginia'),
            ('WA', 'Washington'),
            ('WV', 'West Virginia'),
            ('WI', 'Wisconsin'),
            ('WY', 'Wyoming'),
        ],
    )

    other_province_or_state = forms.CharField(
        required=False,
        min_length=2,
        max_length=64,
        widget=forms.TextInput(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
        label=gettext('Other province or state'),
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
        widget=forms.TextInput(),
        label=gettext('Name of source'),
        help_text=gettext('The organization or entity submitting the records')
    )

    source_type = forms.ChoiceField(
        required=True,
        choices=[
            ('Person', gettext('Person')),
            ('Family', gettext('Family')),
            ('Band', gettext('Band')),
            ('Company', gettext('Company')),
            ('Corporation', gettext('Corporation')),
            ('Organization', gettext('Organization')),
            ('Educational Insitution', gettext('Educational Institution')),
            ('Government Office', gettext('Government Office')),
            ('Other', gettext('Other')),
            ('Unknown', gettext('Unknown')),
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
            ('Creator', gettext('Record Creator')),
            ('Donor', gettext('Record Donor')),
            ('Custodian', gettext('Record Holder')),
            ('Other', gettext('Other')),
            ('Unknown', gettext('Unknown')),
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
        return cleaned_data

    accession_title = forms.CharField(
        min_length=2,
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('e.g., Committee Meeting Minutes')
        }),
        label=gettext('Title')
    )

    start_date_of_material = forms.DateField(
        input_formats=[r'%Y-%m-%d'],
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'start_date_picker reduce-form-field-width',
            'autocomplete': 'off',
            'placeholder': 'yyyy-mm-dd',
        }),
        label=gettext('Earliest date'),
        help_text=gettext('Enter the earliest date relevant to the files you\'re transferring.'),
    )

    # This field is intended to be tied to a button in a date picker for the start date
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
        label=gettext('Latest date'),
        help_text=gettext('Enter the latest date relevant to the files you\'re transferring.'),
    )

    # This field is intended to be tied to a button in a date picker for the end date
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
        label=gettext('Language(s)')
    )

    scope_and_content = forms.CharField(
        required=True,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': 'e.g., These files contain images from ...'
        }),
        label=gettext('Description of contents'),
        help_text=gettext('Briefly describe the content of the files you are transferring. '
                          'What do the files contain?')
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
        return cleaned_data

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


class GroupTransferForm(forms.Form):
    def __init__(self, *args, **kwargs):
        users_groups = kwargs.pop('users_groups')
        super().__init__(*args, **kwargs)
        self.fields['group_name'].choices = [
            ('No Group', gettext('-- None Selected --')),
            ('Add New Group', gettext('-- Add New Group --')),
            *[(x.name, x.name) for x in users_groups],
        ]
        self.allowed_group_names = [x[0] for x in self.fields['group_name'].choices]
        self.fields['group_name'].initial = 'No Group'

    def clean(self):
        cleaned_data = super().clean()
        group_name = cleaned_data['group_name']
        if group_name not in self.allowed_group_names:
            self.add_error('group_name', f'Group name "{group_name}" was not in list')
        if group_name == 'Add New Group' and not cleaned_data['new_group_name']:
            self.add_error('new_group_name', 'Group name cannot be empty')
        if group_name == 'Add New Group' and not cleaned_data['group_description']:
            self.add_error('group_description', 'Group description cannot be empty')
        return cleaned_data

    group_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
        label=gettext('Assigned group')
    )

    new_group_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': gettext('e.g., My Group'),
            }
        ),
        label=gettext('New group name'),
    )

    group_description = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': gettext('e.g., this group represents all of the records from...'),
        }),
        label=gettext('New group description'),
    )


class UploadFilesForm(forms.Form):
    ''' The form where users upload their files and write any final notes '''
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

    session_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        label='hidden'
    )
