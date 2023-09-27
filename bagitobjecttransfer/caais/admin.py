''' CAAIS metadata administrator
'''
from django.contrib import admin

from caais.forms import (
    MetadataForm,
    InlineIdentifierForm,
    InlineArchivalUnitForm,
    InlineDispositionAuthorityForm,
    InlineSourceOfMaterialForm,
    InlinePreliminaryCustodialHistoryForm,
    InlineExtentStatementForm,
    InlinePreliminaryScopeAndContentForm,
    InlineLanguageOfMaterialForm,
    InlineStorageLocationForm,
    InlineRightsForm,
    InlinePreservationRequirementsForm,
    InlineAppraisalForm,
    InlineAssociatedDocumentationForm,
    InlineGeneralNoteForm,
)
from caais.models import (
    AcquisitionMethod,
    Status,
    Metadata,
    Identifier,
    ArchivalUnit,
    DispositionAuthority,
    SourceType,
    SourceRole,
    SourceConfidentiality,
    SourceOfMaterial,
    PreliminaryCustodialHistory,
    ExtentType,
    ContentType,
    CarrierType,
    ExtentStatement,
    PreliminaryScopeAndContent,
    LanguageOfMaterial,
    StorageLocation,
    RightsType,
    Rights,
    PreservationRequirementsType,
    PreservationRequirements,
    AppraisalType,
    Appraisal,
    AssociatedDocumentationType,
    AssociatedDocumentation,
    GeneralNote,
)


class IdentifierInlineAdmin(admin.StackedInline):
    ''' Admin for editing identifiers inline
    '''

    model = Identifier
    form = InlineIdentifierForm
    show_change_link = False
    max_num = 64
    extra = 0

    def get_queryset(self, request):
        ids = super().get_queryset(request).exclude(identifier_type='Accession Identifier')
        return ids


class ArchivalUnitInlineAdmin(admin.TabularInline):
    ''' Admin for editing archival units inline
    '''
    model = ArchivalUnit
    form = InlineArchivalUnitForm
    show_change_link = False
    max_num = 64
    extra = 0


class DispositionAuthorityInlineAdmin(admin.TabularInline):
    ''' Admin for editing disposition authorities inline
    '''
    model = DispositionAuthority
    form = InlineDispositionAuthorityForm
    show_change_link = False
    max_num = 64
    extra = 0


class SourceOfMaterialInlineAdmin(admin.StackedInline):
    ''' Admin for editing source(s) of material inline
    '''

    class Media:
        ''' JavaScript to load for inline form '''
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.16/jquery.mask.min.js",
            "caais/js/phoneNumberMask.js",
        )

    model = SourceOfMaterial
    form = InlineSourceOfMaterialForm
    show_change_link = False
    min_num = 1
    max_num = 64
    extra = 0


class PreliminaryCustodialHistoryInlineAdmin(admin.TabularInline):
    ''' Admin for editing preliminary custodial histories inline
    '''
    model = PreliminaryCustodialHistory
    form = InlinePreliminaryCustodialHistoryForm
    show_change_link = False
    max_num = 64
    extra = 0


class ExtentStatementInlineAdmin(admin.StackedInline):
    ''' Admin for editing extent statements inline
    '''

    model = ExtentStatement
    form = InlineExtentStatementForm
    show_change_link = False
    max_num = 64
    min_num = 1
    extra = 0


class PreliminaryScopeAndContentInlineAdmin(admin.TabularInline):
    ''' Admin for editing preliminary scope and contents inline
    '''

    model = PreliminaryScopeAndContent
    form = InlinePreliminaryScopeAndContentForm
    show_change_link = False
    max_num = 64
    extra = 0


class LanguageOfMaterialInlineAdmin(admin.TabularInline):
    ''' Admin for editing language of materials inline
    '''

    model = LanguageOfMaterial
    form = InlineLanguageOfMaterialForm
    show_change_link = False
    max_num = 64
    extra = 0


class StorageLocationInlineAdmin(admin.TabularInline):
    ''' Admin for editing storage locations inline
    '''

    model = StorageLocation
    form = InlineStorageLocationForm
    show_change_link = False
    max_num = 64
    extra = 0


class RightsInlineAdmin(admin.StackedInline):
    ''' Admin for editing rights inline
    '''

    model = Rights
    form = InlineRightsForm
    show_change_link = False
    max_num = 64
    extra = 0


class PreservationRequirementsInlineAdmin(admin.StackedInline):
    ''' Admin for editing preservation requirements inline
    '''

    model = PreservationRequirements
    form = InlinePreservationRequirementsForm
    show_change_link = False
    max_num = 64
    extra = 0


class AppraisalInlineAdmin(admin.StackedInline):
    ''' Admin for editing appraisals inline
    '''

    model = Appraisal
    form = InlineAppraisalForm
    show_change_link = False
    max_num = 64
    extra = 0


class AssociatedDocumentationInlineAdmin(admin.StackedInline):
    ''' Admin for editing associated documentation inline
    '''

    model = AssociatedDocumentation
    form = InlineAssociatedDocumentationForm
    show_change_link = False
    max_num = 64
    extra = 0


class GeneralNoteInlineAdmin(admin.TabularInline):
    ''' Admin for editing general notes inline
    '''

    model = GeneralNote
    form = InlineGeneralNoteForm
    show_change_link = False
    max_num = 64
    extra = 0


@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    ''' Main CAAIS metadata model admin. All repeatable fields have an
    associated Inline admin for editing all metadata at once.
    '''

    class Media:
        css = {
            'all': (
                'caais/css/metadataChangeForm.css',
            )
        }

    change_form_template = 'admin/metadata_change_form.html'

    form = MetadataForm

    list_display = [
        'accession_title',
        'repository',
        'acquisition_method',
        'id',
    ]

    inlines = [
        IdentifierInlineAdmin,
        ArchivalUnitInlineAdmin,
        DispositionAuthorityInlineAdmin,
        SourceOfMaterialInlineAdmin,
        PreliminaryCustodialHistoryInlineAdmin,
        ExtentStatementInlineAdmin,
        PreliminaryScopeAndContentInlineAdmin,
        LanguageOfMaterialInlineAdmin,
        StorageLocationInlineAdmin,
        RightsInlineAdmin,
        PreservationRequirementsInlineAdmin,
        AppraisalInlineAdmin,
        AssociatedDocumentationInlineAdmin,
        GeneralNoteInlineAdmin,
    ]


@admin.register(AcquisitionMethod)
@admin.register(Status)
@admin.register(SourceType)
@admin.register(SourceRole)
@admin.register(SourceConfidentiality)
@admin.register(ExtentType)
@admin.register(ContentType)
@admin.register(CarrierType)
@admin.register(RightsType)
@admin.register(PreservationRequirementsType)
@admin.register(AppraisalType)
@admin.register(AssociatedDocumentationType)
class TermAdmin(admin.ModelAdmin):
    ''' Generic administrator for models inheriting from AbstractTerm
    '''

    list_display = [
        'name',
        'id',
    ]

    ordering = ['name']
