"""CAAIS metadata administrator."""

from typing import Any, Mapping, Optional

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.http import HttpRequest
from django.template.response import TemplateResponse

from caais import settings as caais_settings
from caais.forms import (
    InlineAppraisalForm,
    InlineArchivalUnitForm,
    InlineAssociatedDocumentationForm,
    InlineDispositionAuthorityForm,
    InlineExtentStatementForm,
    InlineGeneralNoteForm,
    InlineIdentifierForm,
    InlineLanguageOfMaterialForm,
    InlinePreliminaryCustodialHistoryForm,
    InlinePreliminaryScopeAndContentForm,
    InlinePreservationRequirementsForm,
    InlineRightsForm,
    InlineSourceOfMaterialForm,
    InlineStorageLocationForm,
    MetadataForm,
)
from caais.models import (
    AcquisitionMethod,
    Appraisal,
    AppraisalType,
    ArchivalUnit,
    AssociatedDocumentation,
    AssociatedDocumentationType,
    CarrierType,
    ContentType,
    CreationOrRevisionType,
    DateOfCreationOrRevision,
    DispositionAuthority,
    ExtentStatement,
    ExtentType,
    GeneralNote,
    Identifier,
    LanguageOfMaterial,
    Metadata,
    PreliminaryCustodialHistory,
    PreliminaryScopeAndContent,
    PreservationRequirements,
    PreservationRequirementsType,
    Rights,
    RightsType,
    SourceConfidentiality,
    SourceOfMaterial,
    SourceRole,
    SourceType,
    Status,
    StorageLocation,
)


class IdentifierInlineAdmin(admin.StackedInline):
    """Admin for editing identifiers inline"""

    model = Identifier
    form = InlineIdentifierForm
    show_change_link = False
    max_num = 64
    extra = 0

    def get_queryset(self, request):
        ids = super().get_queryset(request).exclude(identifier_type="Accession Identifier")
        return ids


class ArchivalUnitInlineAdmin(admin.TabularInline):
    """Admin for editing archival units inline"""

    model = ArchivalUnit
    form = InlineArchivalUnitForm
    show_change_link = False
    max_num = 64
    extra = 0


class DispositionAuthorityInlineAdmin(admin.TabularInline):
    """Admin for editing disposition authorities inline"""

    model = DispositionAuthority
    form = InlineDispositionAuthorityForm
    show_change_link = False
    max_num = 64
    extra = 0


class SourceOfMaterialInlineAdmin(admin.StackedInline):
    """Admin for editing source(s) of material inline."""

    model = SourceOfMaterial
    form = InlineSourceOfMaterialForm
    show_change_link = False
    min_num = 1
    max_num = 64
    extra = 0


class PreliminaryCustodialHistoryInlineAdmin(admin.TabularInline):
    """Admin for editing preliminary custodial histories inline"""

    model = PreliminaryCustodialHistory
    form = InlinePreliminaryCustodialHistoryForm
    show_change_link = False
    max_num = 64
    extra = 0


class ExtentStatementInlineAdmin(admin.StackedInline):
    """Admin for editing extent statements inline"""

    model = ExtentStatement
    form = InlineExtentStatementForm
    show_change_link = False
    max_num = 64
    min_num = 1
    extra = 0


class PreliminaryScopeAndContentInlineAdmin(admin.TabularInline):
    """Admin for editing preliminary scope and contents inline"""

    model = PreliminaryScopeAndContent
    form = InlinePreliminaryScopeAndContentForm
    show_change_link = False
    max_num = 64
    extra = 0


class LanguageOfMaterialInlineAdmin(admin.TabularInline):
    """Admin for editing language of materials inline"""

    model = LanguageOfMaterial
    form = InlineLanguageOfMaterialForm
    show_change_link = False
    max_num = 64
    extra = 0


class StorageLocationInlineAdmin(admin.TabularInline):
    """Admin for editing storage locations inline"""

    model = StorageLocation
    form = InlineStorageLocationForm
    show_change_link = False
    max_num = 64
    extra = 0


class RightsInlineAdmin(admin.StackedInline):
    """Admin for editing rights inline"""

    model = Rights
    form = InlineRightsForm
    show_change_link = False
    max_num = 64
    extra = 0


class PreservationRequirementsInlineAdmin(admin.StackedInline):
    """Admin for editing preservation requirements inline"""

    model = PreservationRequirements
    form = InlinePreservationRequirementsForm
    show_change_link = False
    max_num = 64
    extra = 0


class AppraisalInlineAdmin(admin.StackedInline):
    """Admin for editing appraisals inline"""

    model = Appraisal
    form = InlineAppraisalForm
    show_change_link = False
    max_num = 64
    extra = 0


class AssociatedDocumentationInlineAdmin(admin.StackedInline):
    """Admin for editing associated documentation inline"""

    model = AssociatedDocumentation
    form = InlineAssociatedDocumentationForm
    show_change_link = False
    max_num = 64
    extra = 0


class GeneralNoteInlineAdmin(admin.TabularInline):
    """Admin for editing general notes inline"""

    model = GeneralNote
    form = InlineGeneralNoteForm
    show_change_link = False
    max_num = 64
    extra = 0


@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    """Main CAAIS metadata model admin. All repeatable fields have an
    associated Inline admin for editing all metadata at once.
    """

    class Media:
        js = ("https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.16/jquery.mask.min.js",)

    change_form_template = "admin/metadata_change_form.html"

    form = MetadataForm

    list_display = [
        "accession_title",
        "accession_identifier",
        "acquisition_method",
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

    def render_change_form(self, request: HttpRequest, context: Mapping[str, Any], add: bool = False, change: bool = False, form_url: str = "", obj: Optional[Metadata] = None) -> TemplateResponse:
        """Add dates_of_creation_or_revision to the context for the template."""
        if obj:
            context["dates_of_creation_or_revision"] = list(
                obj.dates_of_creation_or_revision.all().order_by("-creation_or_revision_date")
            )
        else:
            context["dates_of_creation_or_revision"] = []
        return super().render_change_form(request, context, add, change, form_url, obj)

    def log_change(self, request: HttpRequest, object: Metadata, message: str) -> LogEntry:
        """Add a DateOfCreationOrRevision model when a change is made.
        This method ensures CAAIS compliance by automatically tracking when metadata
        records are updated through the admin interface.
        """
        log_entry = super().log_change(request, object, message)
        update_type_name = caais_settings.CAAIS_DEFAULT_UPDATE_TYPE
        update_type, _ = CreationOrRevisionType.objects.get_or_create(
            name=update_type_name,
            defaults={"description": "Metadata record updated via admin interface"},
        )
        DateOfCreationOrRevision.objects.create(
            metadata=object,
            creation_or_revision_type=update_type,
            creation_or_revision_agent=request.user.username,
            creation_or_revision_note=log_entry.get_change_message(),
        )
        return log_entry


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
    """Generic administrator for models inheriting from AbstractTerm"""

    list_display = [
        "name",
        "id",
    ]

    ordering = ["name"]
