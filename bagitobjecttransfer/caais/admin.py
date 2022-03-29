''' CAAIS metadata administrator
'''
from django.contrib import admin

from caais.forms import (
    InlineIdentifierForm,
    InlineArchivalUnitForm,
    InlineDispositionAuthorityForm,
)
from caais.models import (
    Status,
    Metadata,
    Identifier,
    ArchivalUnit,
    DispositionAuthority,
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
    ]


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    ''' Administrator to add/change accession statuses
    '''

    list_display = [
        'id',
        'status',
    ]
