from django import forms


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
            'required': 'Phone number is required',
            'invalid': 'Phone number must look like "+1 (999) 999-9999"'
        },
        widget=forms.TextInput(attrs={'placeholder': '+1 (999) 999-9999'},
    ))

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
        widget=forms.TextInput(attrs={'placeholder': 'Enter your organization\'s address (optional)'}),
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': 'Enter a brief description of your uploaded files',
        }),
    )
