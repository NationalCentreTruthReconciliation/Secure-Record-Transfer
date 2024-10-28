from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext

from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from caais.models import (
    AbstractTerm,
    Metadata,
    Appraisal,
    ArchivalUnit,
    AssociatedDocumentation,
    DispositionAuthority,
    ExtentStatement,
    GeneralNote,
    Identifier,
    LanguageOfMaterial,
    PreliminaryCustodialHistory,
    PreliminaryScopeAndContent,
    PreservationRequirements,
    Rights,
    SourceOfMaterial,
    StorageLocation,
)


SelectTermWidget = forms.widgets.Select(attrs={
    'class': 'vTextField',
})


class CaaisModelForm(forms.ModelForm):
    ''' Form for CAAIS models. Automatically adds term help_text on all term
    fields since it is not populated by default.

    Allows the specification of 'required' and 'not_required' fields to override
    the default form behaviour.

    Also allows the specification of 'disabled' fields to disable specific
    fields.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_term_fields()
        self._set_required()
        self._set_not_required()
        self._set_disabled()

    def _update_term_fields(self):
        for field_name in self.fields:
            field = self.fields[field_name]
            if hasattr(field, 'queryset'):
                model = field.queryset.model
                if issubclass(model, AbstractTerm):
                    field.help_text = model._meta.get_field('name').help_text

    def _set_required(self):
        if not hasattr(self.Meta, 'required'):
            return
        for field_name in self.Meta.required:
            field = self.fields.get(field_name, None)
            if field is not None:
                field.required = True

    def _set_not_required(self):
        if not hasattr(self.Meta, 'not_required'):
            return
        for field_name in self.Meta.not_required:
            field = self.fields.get(field_name, None)
            if field is not None:
                field.required = False

    def _set_disabled(self):
        if not hasattr(self.Meta, 'disabled'):
            return
        for field_name in self.Meta.disabled:
            field = self.fields.get(field_name, None)
            if field is not None:
                field.disabled = True


class MetadataForm(CaaisModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            accession_id = self.instance.accession_identifier
            self.fields['accession_identifier'].initial = accession_id

    class Meta:
        model = Metadata
        fields = (
            'accession_title',
            'date_of_materials',
            'accession_identifier',
            'repository',
            'acquisition_method',
            'status',
            'date_of_materials',
            'rules_or_conventions',
            'language_of_accession_record',
        )

        required = (
            'accession_title',
            'date_of_materials',
            'accession_identifier',
        )

        not_required = (
            'acquisition_method',
            'status',
        )

        widgets = {
            'acquisition_method': SelectTermWidget,
            'status': SelectTermWidget,
        }

    accession_identifier = forms.CharField(
        max_length=128,
        required=True,
        help_text='Record an identifier to uniquely identify this accession',
        widget=forms.widgets.TextInput(
            attrs={
                'class': 'vTextField',
            }
        )
    )

    def save(self, commit=True):
        ''' Save the accession identifier input as an Identifier with the type
        name "Accession Identifier"
        '''
        metadata: Metadata = super().save(commit=commit)

        accession_id = self.cleaned_data['accession_identifier']

        if accession_id and not metadata.accession_identifier:
            # Need to save model in case commit=False
            metadata.save()
            new_id = Identifier(
                metadata=metadata,
                identifier_type='Accession Identifier',
                identifier_value=accession_id,
            )
            new_id.save()

        elif accession_id != metadata.accession_identifier:
            metadata.update_accession_id(accession_id)

        return metadata


class InlineIdentifierForm(CaaisModelForm):
    class Meta:
        model = Identifier
        fields = '__all__'

        required = (
            'identifier_value',
        )

        widgets = {
            'identifier_note': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
        }

    def clean_identifier_type(self):
        ''' Don't allow a duplicate accession identifier to be specified
        '''
        data = self.cleaned_data['identifier_type']
        if data.lower() == 'accession identifier':
            raise ValidationError(f'{data} is a reserved Identifier type - please use another type name')
        return data


class InlineArchivalUnitForm(CaaisModelForm):
    class Meta:
        model = ArchivalUnit
        fields = '__all__'

        widgets = {
            'archival_unit': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }


class InlineDispositionAuthorityForm(CaaisModelForm):
    class Meta:
        model = DispositionAuthority
        fields = '__all__'

        widgets = {
            'disposition_authority': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }


class InlineSourceOfMaterialForm(CaaisModelForm):
    class Meta:
        model = SourceOfMaterial
        fields = '__all__'

        required = (
            'source_name',
            'email_address',
        )

        not_required = (
            'phone_number',
            'source_type',
            'source_role',
            'source_confidentiality',
        )

        widgets = {
            'source_type': SelectTermWidget,
            'source_role': SelectTermWidget,
            'source_note': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
            'source_confidentiality': SelectTermWidget
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


class InlinePreliminaryCustodialHistoryForm(CaaisModelForm):
    class Meta:
        model = PreliminaryCustodialHistory
        fields = '__all__'

        widgets = {
            'preliminary_custodial_history': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }


class InlineExtentStatementForm(CaaisModelForm):
    class Meta:
        model = ExtentStatement
        fields = '__all__'

        required = (
            'quantity_and_unit_of_measure',
        )

        not_required = (
            'extent_type',
            'content_type',
            'carrier_type',
        )

        widgets = {
            'extent_type': SelectTermWidget,
            'quantity_and_unit_of_measure': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
            'content_type': SelectTermWidget,
            'carrier_type': SelectTermWidget,
            'extent_note': forms.widgets.Textarea(attrs={
                'rows': 1,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
        }


class InlinePreliminaryScopeAndContentForm(CaaisModelForm):
    class Meta:
        model = PreliminaryScopeAndContent
        fields = '__all__'

        widgets = {
            'preliminary_scope_and_content': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }


class InlineLanguageOfMaterialForm(CaaisModelForm):
    class Meta:
        model = LanguageOfMaterial
        fields = '__all__'

        widgets = {
            'language_of_material': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }


class InlineStorageLocationForm(CaaisModelForm):
    class Meta:
        model = StorageLocation
        fields = '__all__'

        widgets = {
            'storage_location': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }


class InlineRightsForm(CaaisModelForm):
    class Meta:
        model = Rights
        fields = '__all__'

        required = (
            'rights_value',
        )

        not_required = (
            'rights_type',
        )

        widgets = {
            'rights_type': SelectTermWidget,
            'rights_value': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
            'rights_note': forms.widgets.Textarea(attrs={
                'rows': 1,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
        }


class InlinePreservationRequirementsForm(CaaisModelForm):
    class Meta:
        model = PreservationRequirements
        fields = '__all__'

        required = (
            'preservation_requirements_value',
        )

        not_required = (
            'preservation_requirements_type',
        )

        widgets = {
            'preservation_requirements_type': SelectTermWidget,
            'preservation_requirements_value': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
            'preservation_requirements_note': forms.widgets.Textarea(attrs={
                'rows': 1,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
        }


class InlineAppraisalForm(CaaisModelForm):
    class Meta:
        model = Appraisal
        fields = '__all__'

        required = (
            'appraisal_value',
        )

        not_required = (
            'appraisal_type',
        )

        widgets = {
            'appraisal_type': SelectTermWidget,
            'appraisal_value': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
            'appraisal_note': forms.widgets.Textarea(attrs={
                'rows': 1,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
        }


class InlineAssociatedDocumentationForm(CaaisModelForm):
    class Meta:
        model = AssociatedDocumentation
        fields = '__all__'

        required = (
            'associated_documentation_title',
        )

        not_required = (
            'associated_documentation_type',
        )

        widgets = {
            'associated_documentation_type': SelectTermWidget,
            'associated_documentation_value': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
            'associated_documentation_note': forms.widgets.Textarea(attrs={
                'rows': 1,
                'class': 'vLargeTextField enable-vertical-resize',
            }),
        }


class InlineGeneralNoteForm(CaaisModelForm):
    class Meta:
        model = GeneralNote
        fields = '__all__'

        widgets = {
            'general_note': forms.widgets.Textarea(attrs={
                'rows': 2,
                'class': 'inline-textarea enable-vertical-resize',
            })
        }
