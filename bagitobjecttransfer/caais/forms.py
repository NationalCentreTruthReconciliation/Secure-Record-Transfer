from django import forms
from django.utils.translation import gettext

from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from caais.models import (
    Identifier,
    ArchivalUnit,
    DispositionAuthority,
    SourceOfMaterial,
    PreliminaryCustodialHistory,
    ExtentStatement,
    PreliminaryScopeAndContent,
    LanguageOfMaterial,
    StorageLocation,
    Rights,
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
                'rows': 2,
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


class InlineExtentStatementForm(forms.ModelForm):
    ''' Form to edit extent statements inline in administrator website
    '''

    class Meta:
        model = ExtentStatement

        fields = '__all__'

        widgets = {
            'extent_note': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField'
            })
        }


class InlinePreliminaryScopeAndContentForm(forms.ModelForm):
    ''' Form to edit preliminary scope and contents inline in administrator
    website
    '''

    class Meta:
        model = PreliminaryScopeAndContent

        fields = (
            'preliminary_scope_and_content',
        )

        widgets = {
            'preliminary_scope_and_content': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            })
        }


class InlineLanguageOfMaterialForm(forms.ModelForm):
    ''' Form to edit language of materials inline in administrator website
    '''

    class Meta:
        model = LanguageOfMaterial

        fields = (
            'language_of_material',
        )

        widgets = {
            'language_of_material': forms.widgets.Textarea(attrs={
                'rows': 1,
                'class': 'inline-textarea',
            })
        }


class InlineStorageLocationForm(forms.ModelForm):
    ''' Form to edit storage locations inline in administrator website
    '''

    class Meta:
        model = StorageLocation

        fields = (
            'storage_location',
        )

        widgets = {
            'storage_location': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            })
        }


class InlineRightsForm(forms.ModelForm):
    ''' Form to edit rights inline in administrator website
    '''

    class Meta:
        model = Rights

        fields = '__all__'

        widgets = {
            'rights_value': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            }),
            'rights_note': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea',
            }),
        }
