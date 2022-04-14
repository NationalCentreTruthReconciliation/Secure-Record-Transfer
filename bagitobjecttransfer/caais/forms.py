from django import forms
from django.utils.translation import gettext

from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from caais.models import (
    Identifier,
    ArchivalUnit,
    DispositionAuthority,
    SourceOfMaterial,
    SourceRole,
    SourceType,
    SourceConfidentiality,
    PreliminaryCustodialHistory,
)


class InlineIdentifierForm(forms.ModelForm):
    ''' Form to edit identifiers inline in administrator website
    '''

    class Meta:
        model = Identifier

        fields = (
            'identifier_type',
            'identifier_value',
            'identifier_note',
        )

        widgets = {
            'identifier_type': forms.widgets.TextInput(attrs={
                'class': 'inline-text-input',
            }),
            'identifier_value': forms.widgets.TextInput(attrs={
                'class': 'inline-text-input',
            }),
            'identifier_note': forms.widgets.Textarea(attrs={
                'rows': 3,
                'class': 'inline-textarea',
            }),
        }


class InlineArchivalUnitForm(forms.ModelForm):
    ''' Form to edit archival units inline in administrator website
    '''

    class Meta:
        model = ArchivalUnit

        fields = (
            'archival_unit',
        )

        widgets = {
            'archival_unit': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            })
        }


class InlineDispositionAuthorityForm(forms.ModelForm):
    ''' Form to edit disposition authorities inline in administrator website
    '''

    class Meta:
        model = DispositionAuthority

        fields = (
            'disposition_authority',
        )

        widgets = {
            'disposition_authority': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            })
        }


class InlineSourceOfMaterialForm(forms.ModelForm):
    ''' Form to edit sources of material inline in administrator website
    '''

    class Meta:
        model = SourceOfMaterial
        fields = '__all__'

        widgets = {
            'source_note': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField',
            })
        }

    source_role = forms.ModelChoiceField(
        queryset=SourceRole.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'vTextField',
            }
        )
    )

    source_type = forms.ModelChoiceField(
        queryset=SourceType.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'vTextField',
            }
        )
    )

    source_confidentiality = forms.ModelChoiceField(
        queryset=SourceConfidentiality.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'vTextField',
            }
        )
    )

    phone_number = forms.RegexField(
        regex=r'^\+\d\s\(\d{3}\)\s\d{3}-\d{4}$',
        error_messages={
            'required': gettext('This field is required.'),
            'invalid': gettext('Phone number must look like "+1 (999) 999-9999"')
        },
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (999) 999-9999',
            'class': 'vTextField',
        }),
        label=gettext('Phone number'),
    )

    email_address = forms.EmailField(
        label=gettext('Email'),
        widget=forms.TextInput(attrs={
            'placeholder': 'person@example.com',
            'class': 'vTextField',
        }),
    )

    country = CountryField(blank_label=gettext('Select a Country')).formfield(
        required=False,
        widget=CountrySelectWidget(
            attrs={
                'class': 'vTextField',
            }
        )
    )


class InlinePreliminaryCustodialHistoryForm(forms.ModelForm):
    ''' Form to edit preliminary custodial histories inline in administrator
    website
    '''

    class Meta:
        model = PreliminaryCustodialHistory

        fields = (
            'preliminary_custodial_history',
        )

        widgets = {
            'preliminary_custodial_history': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            })
        }
