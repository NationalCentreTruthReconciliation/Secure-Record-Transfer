''' Forms specific to transferring files with a new submission '''
from captcha.widgets import ReCaptchaV2Invisible
from django import forms
from django.db.models import Case, When, Value, CharField
from django.forms import BaseFormSet
from django.utils.translation import gettext

from captcha.fields import ReCaptchaField
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from caais.models import SourceType, SourceRole, RightsType
from recordtransfer import settings


class TransferForm(forms.Form):
    required_css_class = 'required-field'


class AcceptLegal(TransferForm):
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['agreement_accepted']:
            self.add_error('agreement_accepted', 'You must accept before continuing')

    agreement_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(),
        label=gettext('I accept these terms'),
    )


class ContactInfoForm(TransferForm):
    ''' The Contact Information portion of the form. Contains fields from Section 2 of CAAIS '''
    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data['province_or_state']
        if region.lower() == 'other' and not cleaned_data['other_province_or_state']:
            self.add_error('other_province_or_state',
                           'This field must be filled out if "Other" province or state is selected')
        elif region.lower() == '':
            self.add_error('province_or_state',
                           'You must select a province or state, use "Other" to enter a custom location')
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
        required=False,
        label=gettext('Job title'),
    )

    organization = forms.CharField(
        max_length=64,
        min_length=2,
        required=False,
        label=gettext('Organization'),
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
            ('', gettext("Select your province")),
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


class SourceInfoForm(TransferForm):
    ''' The Source Information portion of the form. Contains fields from Section 2 of CAAIS '''
    def clean(self):
        cleaned_data = super().clean()

        source_type = cleaned_data.get('source_type', None)
        other_source_type = cleaned_data.get('other_source_type', '')

        if (not source_type or source_type.name.lower() == 'other') and not other_source_type:
            self.add_error('source_type', gettext(
                'If "Other source type" is empty, you must choose one of the '
                'Source types here'
            ))
            self.add_error('other_rights_type', gettext(
                'If "Source type" is Other, you must enter a different type '
                'here'
            ))

        source_role = cleaned_data.get('source_role', None)
        other_source_role = cleaned_data.get('other_source_role', '')
        if (not source_role or source_role.name.lower() == 'other') and not other_source_role:
            self.add_error('source_role', gettext(
                'If "Other source role" is empty, you must choose one of the '
                'Source roles here'
            ))
            self.add_error('other_source_role', gettext(
                'If "Source role" is Other, you must enter a different type '
                'here'
            ))

        return cleaned_data


    source_name = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(),
        label=gettext('Name of source'),
        help_text=gettext('The organization or entity submitting the records')
    )

    source_type = forms.ModelChoiceField(
        required=True,
        queryset=SourceType.objects.all()\
            .annotate(
                sort_order_other_first=Case(
                    When(name__iexact='other', then=Value('____')),
                    default='name',
                    output_field=CharField(),
                )
            )\
            .order_by('sort_order_other_first'),
        empty_label=gettext('Please select one'),
        label=gettext('Source type *'),
        help_text=gettext(
            'How would you describe <b>what</b> the source entity is? '
            'i.e., The source is a(n) ______'
        ),
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        ),
    )

    other_source_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('A source type not covered by the other choices'),
            'class': 'source-type-select-other',
        }),
        label=gettext('Other source type'),
    )

    source_role = forms.ModelChoiceField(
        required=True,
        queryset=SourceRole.objects.all()\
            .annotate(
                sort_order_other_first=Case(
                    When(name__iexact='other', then=Value('____')),
                    default='name',
                    output_field=CharField(),
                )
            )\
            .order_by('sort_order_other_first'),
        empty_label=gettext('Please select one'),
        label=gettext('Source role **'),
        help_text=gettext('How does the source relate to the records? '),
        widget=forms.Select(
            attrs={
                'class': 'reduce-form-field-width',
            }
        )
    )

    other_source_role = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('A source role not covered by the other choices'),
            'class': 'source-role-select-other',
        }),
        label=gettext('Other source role'),
    )

    source_note = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': gettext('Enter any notes you think may be useful for the archives to '
                                   'have about this entity (optional)')
        }),
        label=gettext('Source notes'),
        help_text=gettext('e.g., The donor wishes to remain anonymous')
    )

    preliminary_custodial_history = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': gettext('Enter any information you have on the history of who has had '
                                   'custody of the records or who has kept the records in the past '
                                   '(optional)')
        }),
        label=gettext('Custodial history'),
        help_text=gettext('e.g., John Doe held these records before donating them in 1960'),
    )


class RecordDescriptionForm(TransferForm):
    ''' The Description Information portion of the form. Contains fields from Section 3 of CAAIS '''

    def clean(self):
        ''' Clean form data, and create a date_of_materials field derived from the start and end
        date fields.
        '''
        cleaned_data = super().clean()

        err = False

        if not settings.USE_DATE_WIDGETS:
            start_date_text = cleaned_data['start_date_of_material_text']
            end_date_text = cleaned_data['end_date_of_material_text']

        else:
            start_date = cleaned_data.get('start_date_of_material')
            end_date = cleaned_data.get('end_date_of_material')

            err = False

            if not start_date:
                self.add_error('start_date_of_material', 'Start date was not valid')
                err = True

            if not end_date:
                self.add_error('end_date_of_material', 'End date was not valid')
                err = True

            if start_date and end_date and end_date < start_date:
                self.add_error('end_date_of_material', 'End date cannot be before start date')
                err = True

            if not err:
                start_date_text = start_date.strftime(r'%Y-%m-%d')
                end_date_text = end_date.strftime(r'%Y-%m-%d')

        if not err:
            if cleaned_data.get('start_date_is_approximate', False):
                start_date_text = settings.APPROXIMATE_DATE_FORMAT.format(date=start_date_text)
            if cleaned_data.get('end_date_is_approximate', False):
                end_date_text = settings.APPROXIMATE_DATE_FORMAT.format(date=end_date_text)

            if start_date == end_date:
                cleaned_data['date_of_materials'] = start_date
            else:
                cleaned_data['date_of_materials'] = f'{start_date} - {end_date}'

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

    if not settings.USE_DATE_WIDGETS:
        # Use _text to avoid jQuery input masks
        start_date_of_material_text = forms.CharField(
            min_length=2,
            max_length=64,
            required=True,
            widget=forms.TextInput(attrs={
                'placeholder': gettext('e.g., 2000-03-14')
            }),
            label=gettext('Earliest date'),
            help_text=gettext('Enter the earliest date relevant to the files you\'re transferring.'),
        )
        end_date_of_material_text = forms.CharField(
            min_length=2,
            max_length=64,
            required=True,
            widget=forms.TextInput(attrs={
                'placeholder': 'e.g., Fall 1925',
            }),
            label=gettext('Latest date'),
            help_text=gettext('Enter the latest date relevant to the files you\'re transferring.'),
        )
        start_date_is_approximate = False
        end_date_is_approximate = False

    else:
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
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('English, French')
        }),
        help_text=gettext('Enter all relevant languages here'),
        label=gettext('Language(s)')
    )

    preliminary_scope_and_content = forms.CharField(
        required=True,
        min_length=4,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': 'e.g., These files contain images from ...'
        }),
        label=gettext('Description of contents'),
        help_text=gettext('Briefly describe the content of the files you are transferring. '
                          'What do the files contain?')
    )

    condition_assessment = forms.CharField(
        required=False,
        min_length=4,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': 'e.g., The documents are photocopies ... (optional)'
        }),
        label=gettext('Condition of files'),
        help_text=gettext('Briefly describe the condition of the files you are transferring.')
    )


class ExtendedRecordDescriptionForm(RecordDescriptionForm):
    ''' Adds quantity and type of units to record description form. Intended to be used when file
    uploads are disabled.
    '''

    quantity_and_unit_of_measure = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': gettext('Record how many files and of what type they are that you '
                                   'are planning on transferring (optional)')
        }),
        help_text=gettext('For example, "200 PDF documents, totalling 2.0GB"'),
        label=gettext('Quantity and type of files'),
    )


class RightsFormSet(BaseFormSet):
    """ Special formset to enforce at least one rights form to have a value """
    def __init__(self, *args, **kwargs):
        super(RightsFormSet, self).__init__(*args, **kwargs)
        self.forms[0].empty_permitted = False


class RightsForm(TransferForm):
    ''' The Rights portion of the form. Contains fields from Section 4 of CAAIS '''

    def clean(self):
        cleaned_data = super().clean()

        rights_type = cleaned_data.get('rights_type', None)
        other_rights_type = cleaned_data.get('other_rights_type', '')

        if not rights_type and not other_rights_type:
            self.add_error('rights_type', gettext(
                'If "Other type of rights" is empty, you must choose one of the '
                'Rights types here'
            ))
            self.add_error('other_rights_type', gettext(
                'If "Type of rights" is empty, you must enter a different type '
                'here'
            ))

        return cleaned_data

    rights_type = forms.ModelChoiceField(
        queryset=RightsType.objects.all()\
            .annotate(
                sort_order_other_first=Case(
                    When(name__iexact='other', then=Value('____')),
                    default='name',
                    output_field=CharField(),
                )
            )\
            .order_by('sort_order_other_first'),
        label=gettext('Type of rights'),
        empty_label=gettext('Please select one')
    )

    other_rights_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Other type of rights not covered by other choices'),
            'class': 'rights-select-other',
        }),
        help_text=gettext('For example: "UK Human Rights Act 1998"'),
        label=gettext('Other type of rights'),
    )

    rights_value = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': '2',
            'placeholder': gettext('Any notes on these rights or which files they may apply to '
                                   '(optional)'),
        }),
        help_text=gettext('For example: "Copyright until 2050," "Only applies to images," etc.'),
        label=gettext('Notes for rights')
    )

    '''
    rights_note = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label='hidden'
    )
    '''

class OtherIdentifiersForm(TransferForm):
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


class GroupTransferForm(TransferForm):
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


class UploadFilesForm(TransferForm):
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

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible, label='hidden')


class FinalStepFormNoUpload(TransferForm):
    ''' The form where users write any final notes. Intended to be used in place of UploadFilesForm
    when file uploads are disabled.
    '''

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
