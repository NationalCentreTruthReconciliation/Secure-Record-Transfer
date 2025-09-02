"""Registers models to the admin site."""

from datetime import datetime
from typing import Callable, Sequence

from django.contrib import admin
from django.contrib.admin import display
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe
from django.utils.translation import gettext_lazy as _
from utility import get_human_readable_size

from .models import BaseUploadedFile, PermUploadedFile, TempUploadedFile, UploadSession


def linkify(field_name: str) -> Callable:
    """Convert a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """

    def _linkify(obj: object):
        try:
            linked_obj = getattr(obj, field_name)
            if not linked_obj:
                return "-"

            app_label = linked_obj._meta.app_label
            model_name = linked_obj._meta.model_name
            view_name = f"admin:{app_label}_{model_name}_change"
            link_url = reverse(view_name, args=[linked_obj.pk])
            return format_html('<a href="{}">{}</a>', link_url, linked_obj)

        except AttributeError:
            return "-"

    return admin.display(description=field_name.replace("_", " "))(_linkify)


class BaseUploadedFileAdminMixin:
    """Adds functions for rendering extra fields for uploaded files."""

    @display(description=_("Upload Size"))
    def formatted_upload_size(self, obj: BaseUploadedFile) -> str:
        """Format file size of an BaseUploadedFile instance for display."""
        if not obj.file_upload or not obj.exists:
            return "N/A"
        return get_human_readable_size(int(obj.file_upload.size), 1000, 2)

    @display(description=_("File Link"))
    def uploaded_file_url(self, obj: BaseUploadedFile) -> SafeText:
        """Return the URL to access the file, or a message if the file was removed."""
        if not obj.file_upload or not obj.exists:
            return mark_safe(_("File was removed"))
        return format_html(
            '<a target="_blank" href="{}">{}</a>', obj.get_file_access_url(), obj.name
        )


class BaseUploadedFileAdmin(BaseUploadedFileAdminMixin, admin.ModelAdmin):
    """Regular admin for uploaded files."""

    def has_add_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether add permission is granted for this model admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether change permission is granted for this model admin."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin."""
        return False


class BaseUploadedFileInlineAdmin(BaseUploadedFileAdminMixin, admin.TabularInline):
    """Inline admin for uploaded files."""

    def has_add_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether add permission is granted for this model admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether change permission is granted for this model admin."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin."""
        return False


@admin.register(PermUploadedFile)
class UploadedFileAdmin(BaseUploadedFileAdmin):
    """Admin for a BaseUploadedFile model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    fields: Sequence[str | Sequence[str]] = [
        "id",
        "name",
        "formatted_upload_size",
        "exists",
        "session",
        "uploaded_file_url",
    ]

    list_display: Sequence[str | Callable] = [
        "name",
        "formatted_upload_size",
        "exists",
        linkify("session"),
        "uploaded_file_url",
    ]

    search_fields: Sequence[str] = [
        "name",
        "session__token",
        "session__user__username",
    ]

    ordering: Sequence[str] | None = ["-pk"]


class TempUploadedFileInline(BaseUploadedFileInlineAdmin):
    """Inline admin for the TempUploadedFile model. Used to view the files
    associated with an upload session.

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    model = TempUploadedFile

    fields: Sequence[str | Sequence[str]] = [
        "uploaded_file_url",
        "formatted_upload_size",
        "exists",
    ]

    readonly_fields: Sequence[str | Callable] = [
        "exists",
        "uploaded_file_url",
        "formatted_upload_size",
    ]


class PermUploadedFileInline(BaseUploadedFileInlineAdmin):
    """Inline admin for the PermUploadedFile model. Used to view the files
    associated with an upload session.

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    model = PermUploadedFile

    fields: Sequence[str | Sequence[str]] = [
        "uploaded_file_url",
        "formatted_upload_size",
        "exists",
    ]

    readonly_fields: Sequence[str | Callable] = [
        "exists",
        "uploaded_file_url",
        "formatted_upload_size",
    ]


@admin.register(UploadSession)
class UploadSessionAdmin(admin.ModelAdmin):
    """Admin for the UploadSession model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    fields: Sequence[str | Sequence[str]] = [
        "token",
        "user",
        "started_at",
        "last_upload_at",
        "file_count",
        "upload_size",
        "status",
        "is_expired",
        "expires_at",
    ]

    search_fields: Sequence[str] = [
        "token",
        "user__username",
    ]

    list_display: Sequence[str | Callable] = [
        "token",
        linkify("user"),
        "started_at",
        "last_upload_at",
        "file_count",
        "upload_size",
        "status",
        "is_expired",
        "expires_at",
    ]

    ordering: Sequence[str] | None = [
        "-started_at",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Determine whether add permission is granted for this model admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether change permission is granted for this model admin."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin."""
        return False

    def get_inlines(self, request: HttpRequest, obj: UploadSession | None = None) -> list:
        """Return the inlines to display for the UploadSession."""
        if obj is None:
            return []
        if obj.status in {
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
            UploadSession.SessionStatus.EXPIRED,
        }:
            return [TempUploadedFileInline]
        elif obj.status == UploadSession.SessionStatus.STORED:
            return [PermUploadedFileInline]
        else:
            return [TempUploadedFileInline, PermUploadedFileInline]

    def file_count(self, obj: UploadSession) -> str:
        """Display the number of files uploaded to the session."""
        file_count = None
        try:
            file_count = obj.file_count
        except ValueError:
            file_count = "n/a"
        return str(file_count)

    @display(description=_("Upload Size"))
    def upload_size(self, obj: UploadSession) -> str | None:
        """Display the total upload size for the session."""
        upload_size = None
        try:
            upload_size = get_human_readable_size(obj.upload_size, 1000, 2)
        except ValueError:
            upload_size = "n/a"
        return upload_size

    @display(description=_("Last upload at"))
    def last_upload_at(self, obj: UploadSession) -> datetime:
        """Display the last time a file was uploaded to the session."""
        return obj.last_upload_interaction_time
