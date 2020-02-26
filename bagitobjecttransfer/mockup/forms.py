from django import forms


class TransferForm(forms.Form):
    first_name = forms.CharField(
        max_length=64,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
    )

    last_name = forms.CharField(
        max_length=64,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
    )

    phone_number = forms.RegexField(
        regex=r'^\d{10}$',
        error_messages={
            'invalid': 'Phone number must be in the form "9999999999"'
        }
    )

    email = forms.EmailField()

    organization = forms.CharField(
        max_length=128,
        min_length=2,
        required=False,
    )

    organization_address = forms.CharField(
        max_length=256,
        min_length=8,
        required=False,
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': '4',
            'placeholder': 'Enter a brief description of your uploaded files'
        }),
    )
