from django import forms
from caais.models import (
    Identifier,
    ArchivalUnit,
    DispositionAuthority,
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
