''' CAAIS metadata administrator
'''
from django.contrib import admin

from caais.forms import (
    InlineIdentifierForm,
    InlineArchivalUnitForm,
    InlineDispositionAuthorityForm,
    InlineSourceOfMaterialForm,
    InlinePreliminaryCustodialHistoryForm,
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
        for field_name in ('source_role', 'source_type', 'source_confidentiality'):
            field = formset.form.base_fields[field_name]
            field.required = False
            field.widget.can_add_related = True
            field.widget.can_change_related = True
            field.widget.can_delete_related = True
            field.widget.attrs.update({'class': 'vTextField'})
        return formset


class PreliminaryCustodialHistoryInlineAdmin(admin.TabularInline):
    ''' Admin for editing preliminary custodial histories inline
    '''
    model = PreliminaryCustodialHistory
    form = InlinePreliminaryCustodialHistoryForm
    show_change_link = False
    max_num = 64
    extra = 0


@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    ''' Main CAAIS metadata model admin. All repeatable fields have an
    associated Inline admin for editing all metadata at once.
    '''

    change_form_template = 'admin/metadata_change_form.html'

    list_display = [
        'id',
        'repository',
        'accession_title',
        'acquisition_method',
    ]

    inlines = [
        IdentifierInlineAdmin,
        ArchivalUnitInlineAdmin,
        DispositionAuthorityInlineAdmin,
        SourceOfMaterialInlineAdmin,
        PreliminaryCustodialHistoryInlineAdmin,
    ]


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    ''' Administrator to add/change accession statuses
    '''

    list_display = [
        'id',
        'status',
    ]

@admin.register(SourceRole)
class SourceRoleAdmin(admin.ModelAdmin):
    ''' Administrator to add/change source roles
    '''

    list_display = [
        'id',
        'source_role',
    ]

@admin.register(SourceType)
class SourceTypeAdmin(admin.ModelAdmin):
    ''' Administrator to add/change source types
    '''

    list_display = [
        'id',
        'source_type',
    ]

@admin.register(SourceConfidentiality)
class SourceConfidentialityAdmin(admin.ModelAdmin):
    ''' Administrator to add/change source confidentialies
    '''

    list_display = [
        'id',
        'source_confidentiality',
    ]
