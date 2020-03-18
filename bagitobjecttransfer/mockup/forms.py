from django import forms


class SourceForm(forms.Form):
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
            'Creator',
            'Donor',
            'Custodian',
            'Unknown',
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
        widget=forms.TextInput(
            attrs={'placeholder': 'Enter your name'}
        ),
    )

    job_title = forms.CharField(
        max_length=64,
        min_length=2,
        required=True,
        widget=forms.TextInput(
            attrs={'placeholder': 'Enter your job title'}
        )
    )

    phone_number = forms.RegexField(
        regex=r'^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$',
        error_messages={
            'required': 'This field is required.',
            'invalid': 'Phone number must look like "+1 (999) 999-9999"'
        },
        widget=forms.TextInput(attrs={'placeholder': '+1 (999) 999-9999'},)
    )

    email = forms.EmailField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter your email'}),
    )

class TransferForm(forms.Form):
    first_name = forms.CharField(
        max_length=32,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
    )

    last_name = forms.CharField(
        max_length=32,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
    )

    phone_number = forms.RegexField(
        regex=r'^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$',
        error_messages={
            'required': 'This field is required.',
            'invalid': 'Phone number must look like "+1 (999) 999-9999"'
        },
        widget=forms.TextInput(attrs={'placeholder': '+1 (999) 999-9999'},)
    )

    email = forms.EmailField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter your email'}),
    )

    organization = forms.CharField(
        max_length=128,
        min_length=2,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your organization (optional)'}),
    )

    organization_address = forms.CharField(
        max_length=256,
        min_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your organization\'s address (optional)'
        }),
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': 'Enter a brief description of your uploaded files',
        }),
    )

    session_token = forms.CharField(widget=forms.HiddenInput())
