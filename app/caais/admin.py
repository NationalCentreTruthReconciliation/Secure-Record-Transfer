"""CAAIS metadata administrator."""

from datetime import datetime
from typing import Any, Callable, Mapping, Optional, Sequence

from django.contrib import admin
from django.contrib.admin import ListFilter
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import InlineModelAdmin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from caais import settings as caais_settings
from caais.constants import ACCESSION_IDENTIFIER_TYPE
from caais.db import GroupConcat
from caais.export import ExportVersion
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
from caais.managers import MetadataQuerySet
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
    """Admin for editing identifiers inline."""

    model = Identifier
    form = InlineIdentifierForm
    show_change_link = False
    max_num = 64
    extra = 0

    def get_queryset(self, request: HttpRequest) -> QuerySet[Identifier]:
        """Exclude accession identifiers from the queryset."""
        ids = super().get_queryset(request).exclude(identifier_type=ACCESSION_IDENTIFIER_TYPE)
        return ids


class ArchivalUnitInlineAdmin(admin.TabularInline):
    """Admin for editing archival units inline."""

    model = ArchivalUnit
    form = InlineArchivalUnitForm
    show_change_link = False
    max_num = 64
    extra = 0


class DispositionAuthorityInlineAdmin(admin.TabularInline):
    """Admin for editing disposition authorities inline."""

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
    """Admin for editing preliminary custodial histories inline."""

    model = PreliminaryCustodialHistory
    form = InlinePreliminaryCustodialHistoryForm
    show_change_link = False
    max_num = 64
    extra = 0


class ExtentStatementInlineAdmin(admin.StackedInline):
    """Admin for editing extent statements inline."""

    model = ExtentStatement
    form = InlineExtentStatementForm
    show_change_link = False
    max_num = 64
    min_num = 1
    extra = 0


class PreliminaryScopeAndContentInlineAdmin(admin.TabularInline):
    """Admin for editing preliminary scope and contents inline."""

    model = PreliminaryScopeAndContent
    form = InlinePreliminaryScopeAndContentForm
    show_change_link = False
    max_num = 64
    extra = 0


class LanguageOfMaterialInlineAdmin(admin.TabularInline):
    """Admin for editing language of materials inline."""

    model = LanguageOfMaterial
    form = InlineLanguageOfMaterialForm
    show_change_link = False
    max_num = 64
    extra = 0


class StorageLocationInlineAdmin(admin.TabularInline):
    """Admin for editing storage locations inline."""

    model = StorageLocation
    form = InlineStorageLocationForm
    show_change_link = False
    max_num = 64
    extra = 0


class RightsInlineAdmin(admin.StackedInline):
    """Admin for editing rights inline."""

    model = Rights
    form = InlineRightsForm
    show_change_link = False
    max_num = 64
    extra = 0


class PreservationRequirementsInlineAdmin(admin.StackedInline):
    """Admin for editing preservation requirements inline."""

    model = PreservationRequirements
    form = InlinePreservationRequirementsForm
    show_change_link = False
    max_num = 64
    extra = 0


class AppraisalInlineAdmin(admin.StackedInline):
    """Admin for editing appraisals inline."""

    model = Appraisal
    form = InlineAppraisalForm
    show_change_link = False
    max_num = 64
    extra = 0


class AssociatedDocumentationInlineAdmin(admin.StackedInline):
    """Admin for editing associated documentation inline."""

    model = AssociatedDocumentation
    form = InlineAssociatedDocumentationForm
    show_change_link = False
    max_num = 64
    extra = 0


class GeneralNoteInlineAdmin(admin.TabularInline):
    """Admin for editing general notes inline."""

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
        """Static assets for the Metadata admin."""

        js = ("https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.16/jquery.mask.min.js",)

    change_form_template = "admin/metadata_change_form.html"

    form = MetadataForm

    list_display: Sequence[str | Callable] = [
        "accession_title",
        "accession_identifier",
        "source_name",
        "status",
        "last_changed",
    ]

    list_filter: Sequence[str | type[ListFilter] | tuple[str, type[ListFilter]]] = [
        "status",
    ]

    search_fields: Sequence[str] = [
        "identifiers__identifier_value",
        "source_of_materials__source_name",
        "source_of_materials__contact_name",
        "source_of_materials__organization",
        "status__name",
        "accession_title",
        "repository",
    ]

    inlines: Sequence[type[InlineModelAdmin]] = [
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

    actions: (
        Sequence[Callable[[Any, HttpRequest, QuerySet[Any]], HttpResponse | None] | str] | None
    ) = [
        "export_caais_csv",
        "export_atom_2_6_csv",
        "export_atom_2_3_csv",
        "export_atom_2_2_csv",
        "export_atom_2_1_csv",
    ]

    def source_name(self, obj: Metadata) -> Optional[str]:
        """Return a comma-separated list of source names."""
        return obj.source_of_materials.aggregate(
            names_joined=GroupConcat("source_name", separator=", ")
        )["names_joined"]

    def last_changed(self, obj: Metadata) -> Optional[datetime]:
        """Return the date the metadata was last changed."""
        most_recent = obj.dates_of_creation_or_revision.order_by(
            "-creation_or_revision_date"
        ).first()
        if most_recent:
            return most_recent.creation_or_revision_date
        return None

    def render_change_form(
        self,
        request: HttpRequest,
        context: Mapping[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Optional[Metadata] = None,
    ) -> TemplateResponse:
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

    @admin.action(description=_("Export CAAIS 1.0 CSV for Selected"))
    def export_caais_csv(self, request: HttpRequest, queryset: MetadataQuerySet) -> HttpResponse:
        """Export CAAIS 1.0 CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.CAAIS_1_0)

    @admin.action(description=_("Export AtoM 2.6 Accession CSV for Selected"))
    def export_atom_2_6_csv(
        self, request: HttpRequest, queryset: MetadataQuerySet
    ) -> HttpResponse:
        """Export AtoM 2.6 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_6)

    @admin.action(description=_("Export AtoM 2.3 Accession CSV for Selected"))
    def export_atom_2_3_csv(
        self, request: HttpRequest, queryset: MetadataQuerySet
    ) -> HttpResponse:
        """Export AtoM 2.3 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_3)

    @admin.action(description=_("Export AtoM 2.2 Accession CSV for Selected"))
    def export_atom_2_2_csv(
        self, request: HttpRequest, queryset: MetadataQuerySet
    ) -> HttpResponse:
        """Export AtoM 2.2 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_2)

    @admin.action(description=_("Export AtoM 2.1 Accession CSV for Selected"))
    def export_atom_2_1_csv(
        self, request: HttpRequest, queryset: MetadataQuerySet
    ) -> HttpResponse:
        """Export AtoM 2.1 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_1)


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
    """Generic administrator for models inheriting from AbstractTerm."""

    list_display: Sequence[str | Callable] = [
        "name",
        "id",
    ]

    ordering: Sequence[str] | None = ["name"]
