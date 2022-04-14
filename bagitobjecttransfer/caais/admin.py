''' CAAIS metadata administrator
'''
from django.contrib import admin

from caais.forms import (
    InlineIdentifierForm,
    InlineArchivalUnitForm,
    InlineDispositionAuthorityForm,
    InlineSourceOfMaterialForm,
    InlinePreliminaryCustodialHistoryForm,
    InlineExtentStatementForm,
    InlinePreliminaryScopeAndContentForm,
    InlineLanguageOfMaterialForm,
)
from caais.models import (
    Status,
    Metadata,
    Identifier,
    ArchivalUnit,
    DispositionAuthority,
    SourceRole,
    SourceType,
    SourceConfidentiality,
    SourceOfMaterial,
    PreliminaryCustodialHistory,
    ExtentStatement,
    ExtentType,
    ContentType,
    CarrierType,
    PreliminaryScopeAndContent,
    LanguageOfMaterial,
)


class IdentifierInlineAdmin(admin.TabularInline):
    ''' Admin for editing identifiers inline
    '''
    model = Identifier
    form = InlineIdentifierForm
    show_change_link = False
    max_num = 64
    extra = 0


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
    max_num = 64
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field_name, model in (
                ('source_role', SourceRole),
                ('source_type', SourceType),
                ('source_confidentiality', SourceConfidentiality),
            ):
            field = formset.form.base_fields[field_name]
            field.required = False
            field.widget.can_add_related = True
            field.widget.can_change_related = True
            field.widget.can_delete_related = True
            field.widget.attrs.update({'class': 'vTextField'})
            field.help_text = model._meta.get_field('name').help_text
        return formset


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
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for field_name, model, required in (
                ('extent_type', ExtentType, True),
                ('content_type', ContentType, False),
                ('carrier_type', CarrierType, False),
            ):
            field = formset.form.base_fields[field_name]
            field.required = required
            field.widget.can_add_related = True
            field.widget.can_change_related = True
            field.widget.can_delete_related = True
            field.widget.attrs.update({'class': 'vTextField'})
            field.help_text = model._meta.get_field('name').help_text
        return formset


class PreliminaryScopeAndContentInlineAdmin(admin.TabularInline):
    ''' Admin for editing preliminary scope and contents inline
    '''

    model = PreliminaryScopeAndContent
    form = InlinePreliminaryScopeAndContentForm
    show_change_link = False
    max_num = 64
    extra = 0


class LanguageOfMaterialInlineAdmin(admin.TabularInline):
    ''' Admin for editing language of materials inlines
    '''

    model = LanguageOfMaterial
    form = InlineLanguageOfMaterialForm
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
                'caais/css/inlineTextInputs.css',
            )
        }

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
    ]


class TermAdmin(admin.ModelAdmin):
    ''' Generic administrator for models inheriting from AbstractTerm
    '''

    list_display = [
        'name',
        'id',
    ]

    ordering = ['-id']


@admin.register(Status)
class StatusAdmin(TermAdmin):
    ''' Administrator to add/change accession statuses
    '''


@admin.register(SourceRole)
class SourceRoleAdmin(TermAdmin):
    ''' Administrator to add/change source roles
    '''


@admin.register(SourceType)
class SourceTypeAdmin(TermAdmin):
    ''' Administrator to add/change source types
    '''


@admin.register(SourceConfidentiality)
class SourceConfidentialityAdmin(TermAdmin):
    ''' Administrator to add/change source confidentialies
    '''


@admin.register(ExtentType)
class ExtentTypeAdmin(TermAdmin):
    ''' Administrator to add/change extent types
    '''


@admin.register(ContentType)
class ContentTypeAdmin(TermAdmin):
    ''' Administrator to add/change content types
    '''


@admin.register(CarrierType)
class CarrierTypeAdmin(TermAdmin):
    ''' Administrator to add/change carrier types
    '''
