from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext
from django_recaptcha.fields import ReCaptchaField

from recordtransfer.forms.admin_forms import *
from recordtransfer.forms.submission_forms import *
from recordtransfer.forms.user_forms import *
from recordtransfer.models import User


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

    captcha = ReCaptchaField()
