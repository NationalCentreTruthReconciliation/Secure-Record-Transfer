"""Custom administration code for the admin site."""

import logging
from datetime import datetime
from typing import Any, Callable, Optional, Sequence, Type, Union

from caais.export import ExportVersion
from django.contrib import admin, messages
from django.contrib.admin import display
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin, sensitive_post_parameters_m
from django.db.models import Model, QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe
from django.utils.translation import gettext

from recordtransfer.constants import HtmlIds, OtherValues
from recordtransfer.emails import send_user_account_updated
from recordtransfer.forms import (
    SubmissionModelForm,
)
from recordtransfer.forms.admin_forms import SiteSettingModelForm, UserAdminForm
from recordtransfer.jobs import create_downloadable_bag
from recordtransfer.models import (
    BaseUploadedFile,
    Job,
    PermUploadedFile,
    SiteSetting,
    Submission,
    SubmissionGroup,
    TempUploadedFile,
    UploadSession,
    User,
)
from recordtransfer.utils import get_human_readable_size

LOGGER = logging.getLogger("recordtransfer")


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


@receiver(pre_delete, sender=Job)
def job_file_delete(sender: Job, instance: Job, **kwargs) -> None:
    """FileFields are not deleted automatically after Django 1.11, instead this receiver does
    it.
    """
    instance.attached_file.delete(False)


@display(description=gettext("Upload Size"))
def format_upload_size(obj: BaseUploadedFile) -> str:
    """Format file size of an BaseUploadedFile instance for display."""
    if not obj.file_upload or not obj.exists:
        return "N/A"
    return get_human_readable_size(int(obj.file_upload.size), 1000, 2)


@display(description=gettext("File Link"))
def uploaded_file_url(obj: BaseUploadedFile) -> SafeText:
    """Return the URL to access the file, or a message if the file was removed."""
    if not obj.file_upload or not obj.exists:
        return mark_safe(gettext("File was removed"))
    return format_html('<a target="_blank" href="{}">{}</a>', obj.get_file_access_url(), obj.name)


class ReadOnlyAdmin(admin.ModelAdmin):
    """A model admin that does not allow any editing/changing/ or deletions.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    readonly_fields: Sequence[Union[str, Callable]] = []

    def get_readonly_fields(self, request: HttpRequest, obj: object = None) -> tuple:
        """Return all fields as read-only for this model admin."""
        meta = obj._meta if isinstance(obj, Model) else self.model._meta
        return (
            tuple(self.readonly_fields)
            + tuple(field.name for field in meta.fields)
            + tuple(field.name for field in meta.many_to_many)
        )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Determine whether add permission is granted for this model admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether change permission is granted for this model admin."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin."""
        return False


class ReadOnlyInline(admin.TabularInline):
    """Inline admin that does not allow any editing/changing/ or deletions.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    max_num = 0
    show_change_link = True

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
class UploadedFileAdmin(ReadOnlyAdmin):
    """Admin for the UploadedFile model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    fields: Sequence[Union[str, Sequence[str]]] = [
        "id",
        "name",
        format_upload_size,
        "exists",
        linkify("session"),
        uploaded_file_url,
    ]

    list_display: Sequence[Union[str, Callable]] = [
        "name",
        format_upload_size,
        "exists",
        linkify("session"),
        uploaded_file_url,
    ]

    search_fields: Sequence[str] = [
        "name",
        "session__token",
        "session__user__username",
    ]

    ordering: Optional[Sequence[str]] = ["-pk"]


class TempUploadedFileInline(ReadOnlyInline):
    """Inline admin for the BaseUploadedFile model. Used to view the files
    associated with an upload session.

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    model = TempUploadedFile

    fields: Sequence[Union[str, Sequence[str]]] = [
        uploaded_file_url,
        format_upload_size,
        "exists",
    ]
    readonly_fields: Sequence[Union[str, Callable]] = [
        "exists",
        uploaded_file_url,
        format_upload_size,
    ]


class PermUploadedFileInline(ReadOnlyInline):
    """Inline admin for the BaseUploadedFile model. Used to view the files
    associated with an upload session.

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    model = PermUploadedFile
    fields: Sequence[Union[str, Sequence[str]]] = [
        uploaded_file_url,
        format_upload_size,
        "exists",
    ]
    readonly_fields: Sequence[Union[str, Callable]] = [
        "exists",
        uploaded_file_url,
        format_upload_size,
    ]


@admin.register(UploadSession)
class UploadSessionAdmin(ReadOnlyAdmin):
    """Admin for the UploadSession model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    fields: Sequence[Union[str, Sequence[str]]] = [
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
    search_fields: Sequence[str] = ["token", "user__username"]
    list_display: Sequence[Union[str, Callable]] = [
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

    ordering: Optional[Sequence[str]] = [
        "-started_at",
    ]

    def get_inlines(self, request: HttpRequest, obj: Optional[UploadSession] = None) -> list:
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

    def file_count(self, obj: UploadSession) -> Union[int, str]:
        """Display the number of files uploaded to the session."""
        file_count = None
        try:
            file_count = obj.file_count
        except ValueError:
            file_count = "n/a"
        return file_count

    @display(description=gettext("Upload Size"))
    def upload_size(self, obj: UploadSession) -> Union[str, None]:
        """Display the total upload size for the session."""
        upload_size = None
        try:
            upload_size = get_human_readable_size(obj.upload_size, 1000, 2)
        except ValueError:
            upload_size = "n/a"
        return upload_size

    @admin.display(description="Last upload at")
    def last_upload_at(self, obj: UploadSession) -> datetime:
        """Display the last time a file was uploaded to the session."""
        return obj.last_upload_interaction_time


class SubmissionInline(ReadOnlyInline):
    """Inline admin for the Submission model.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to Submission page for change ability
        - delete: Only by superusers
    """

    model = Submission

    fields: Sequence[Union[str, Sequence[str]]] = ["uuid", "metadata"]

    ordering: Optional[Sequence[str]] = ["-submission_date"]

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this inline admin.
        Returns True if the object exists and the requesting user is a superuser, otherwise False.
        """
        return bool(obj and request.user.is_superuser)


@admin.register(SubmissionGroup)
class SubmissionGroupAdmin(ReadOnlyAdmin):
    """Admin for the SubmissionGroup model. Submissions can be viewed in-line.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only by superusers
    """

    list_display: Sequence[Union[str, Callable]] = [
        "name",
        linkify("created_by"),
        "number_of_submissions_in_group",
    ]

    inlines: Sequence[Type[InlineModelAdmin]] = [SubmissionInline]

    search_fields: Sequence[str] = [
        "name",
        "uuid",
    ]

    ordering: Optional[Sequence[str]] = [
        "-created_by",
    ]

    actions: Optional[
        Sequence[Union[Callable[[Any, HttpRequest, QuerySet[Any]], Optional[HttpResponse]], str]]
    ] = [
        "export_caais_csv",
        "export_atom_2_6_csv",
        "export_atom_2_3_csv",
        "export_atom_2_2_csv",
        "export_atom_2_1_csv",
    ]

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin.
        Returns True if the object exists and the requesting user is a superuser, otherwise False.
        """
        return bool(obj and request.user.is_superuser)

    def _export_submissions_csv(
        self, request: HttpRequest, queryset: QuerySet[SubmissionGroup], version: ExportVersion
    ) -> Optional[HttpResponse]:
        """Export submissions from selected groups with validation.

        Args:
            request: The HTTP request object
            queryset: QuerySet of selected SubmissionGroup objects
            version: The export version to use

        Returns:
            HttpResponse with CSV file or None if no submissions found
        """
        related_submissions = Submission.objects.filter(part_of_group__in=queryset)
        if not related_submissions.exists():
            self.message_user(
                request,
                gettext(
                    "The selected submission group(s) do not contain any submissions to export."
                ),
                messages.WARNING,
            )
            return None
        return related_submissions.export_csv(version=version)

    @admin.action(description=gettext("Export CAAIS 1.0 CSV for Submissions in Selected"))
    def export_caais_csv(self, request: HttpRequest, queryset: QuerySet) -> Optional[HttpResponse]:
        """Export CAAIS 1.0 CSV for submissions in the selected queryset."""
        return self._export_submissions_csv(request, queryset, ExportVersion.CAAIS_1_0)

    @admin.action(description=gettext("Export AtoM 2.6 Accession CSV for Submissions in Selected"))
    def export_atom_2_6_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> Optional[HttpResponse]:
        """Export AtoM 2.6 Accession CSV for submissions in the selected queryset."""
        return self._export_submissions_csv(request, queryset, ExportVersion.ATOM_2_6)

    @admin.action(description=gettext("Export AtoM 2.3 Accession CSV for Submissions in Selected"))
    def export_atom_2_3_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> Optional[HttpResponse]:
        """Export AtoM 2.3 Accession CSV for submissions in the selected queryset."""
        return self._export_submissions_csv(request, queryset, ExportVersion.ATOM_2_3)

    @admin.action(description=gettext("Export AtoM 2.2 Accession CSV for Submissions in Selected"))
    def export_atom_2_2_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> Optional[HttpResponse]:
        """Export AtoM 2.2 Accession CSV for submissions in the selected queryset."""
        return self._export_submissions_csv(request, queryset, ExportVersion.ATOM_2_2)

    @admin.action(description=gettext("Export AtoM 2.1 Accession CSV for Submissions in Selected"))
    def export_atom_2_1_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> Optional[HttpResponse]:
        """Export AtoM 2.1 Accession CSV for submissions in the selected queryset."""
        return self._export_submissions_csv(request, queryset, ExportVersion.ATOM_2_1)


class SubmissionGroupInline(ReadOnlyInline):
    """Inline admin for viewing submission groups.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to SubmissionGroup page for change ability
        - delete: Not allowed - go to SubmissionGroup page for delete ability
    """

    model = SubmissionGroup
    fields: Sequence[Union[str, Sequence[str]]] = [
        "name",
        "description",
        "number_of_submissions_in_group",
    ]
    # Tells Django this is a computed field
    readonly_fields: Sequence[Union[str, Callable[..., Any]]] = ["number_of_submissions_in_group"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin for the Submission model.

    Permissions:
        - add: Not allowed
        - change: Allowed
        - delete: Only by superusers
    """

    change_form_template = "admin/submission_change_form.html"

    form = SubmissionModelForm

    actions: Optional[
        Sequence[Union[Callable[[Any, HttpRequest, QuerySet[Any]], Optional[HttpResponse]], str]]
    ] = [
        "export_caais_csv",
        "export_atom_2_6_csv",
        "export_atom_2_3_csv",
        "export_atom_2_2_csv",
        "export_atom_2_1_csv",
    ]

    search_fields: Sequence[str] = [
        "uuid",
        "metadata__accession_title",
        "user__username",
        "user__email",
    ]

    list_display: Sequence[Union[str, Callable[..., Any]]] = [
        "submission_date",
        "uuid",
        "file_count",
        linkify("metadata"),
        linkify("user"),
    ]

    ordering: Optional[Sequence[str]] = [
        "-submission_date",
    ]

    readonly_fields: Sequence[Union[str, Callable[..., Any]]] = [
        "submission_date",
        "user",
        "upload_session",
        "part_of_group",
        "uuid",
    ]

    def file_count(self, obj: Submission) -> Union[int, str]:
        """Display the number of files uploaded to the submission."""
        if not obj.upload_session:
            return 0
        file_count = None
        try:
            file_count = obj.upload_session.file_count
        except ValueError:
            file_count = "n/a"
        return file_count

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Determine whether add permission is granted for this model admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether change permission is granted for this model admin."""
        return True

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin."""
        return bool(obj and request.user.is_superuser)

    def get_urls(self) -> list:
        """Add extra views to admin."""
        return [
            path(
                "<path:object_id>/zip/",
                self.admin_site.admin_view(self.create_zipped_bag),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_zip",
            ),
            *super().get_urls(),
        ]

    def create_zipped_bag(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        """Start a background job to create a downloadable bag.

        Args:
            request: The originating request
            object_id: The ID for the submission
        """
        submission = Submission.objects.filter(id=object_id).first()

        if submission and submission.upload_session:
            create_downloadable_bag.delay(submission, User.objects.get(pk=request.user.pk))

            self.message_user(
                request,
                mark_safe(
                    gettext(
                        (
                            'A downloadable bag is being generated. Visit the <a href="{url}">jobs page</a> for '
                            "the status of the bag generation, or check the Submission page for a download link"
                        )
                    ).format(url=reverse("admin:recordtransfer_job_changelist"))
                ),
            )

            return HttpResponseRedirect(submission.get_admin_change_url())

        elif submission and not submission.upload_session:
            self.message_user(
                request,
                gettext(
                    (
                        "There are no files associated with this submission, it is not possible to "
                        "create a Bag"
                    )
                ),
                messages.WARNING,
            )

            return HttpResponseRedirect(submission.get_admin_change_url())

        # Error response
        msg = gettext(f"Submission with ID '{object_id}' doesn't exist. Perhaps it was deleted?")
        self.message_user(request, msg, messages.ERROR)
        admin_url = reverse("admin:index", current_app=self.admin_site.name)
        return HttpResponseRedirect(admin_url)

    @admin.action(description=gettext("Export CAAIS 1.0 CSV for Submissions in Selected"))
    def export_caais_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponseRedirect:
        """Export CAAIS 1.0 CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.CAAIS_1_0)

    @admin.action(description=gettext("Export AtoM 2.6 Accession CSV for Submissions in Selected"))
    def export_atom_2_6_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> HttpResponseRedirect:
        """Export AtoM 2.6 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_6)

    @admin.action(description=gettext("Export AtoM 2.3 Accession CSV for Submissions in Selected"))
    def export_atom_2_3_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> HttpResponseRedirect:
        """Export AtoM 2.3 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_3)

    @admin.action(description=gettext("Export AtoM 2.2 Accession CSV for Submissions in Selected"))
    def export_atom_2_2_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> HttpResponseRedirect:
        """Export AtoM 2.2 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_2)

    @admin.action(description=gettext("Export AtoM 2.1 Accession CSV for Submissions in Selected"))
    def export_atom_2_1_csv(
        self, request: HttpRequest, queryset: QuerySet
    ) -> HttpResponseRedirect:
        """Export AtoM 2.1 Accession CSV for submissions in the selected queryset."""
        return queryset.export_csv(version=ExportVersion.ATOM_2_1)


@admin.register(Job)
class JobAdmin(ReadOnlyAdmin):
    """Admin for the Job model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only superusers
    """

    fields: Sequence[Union[str, Sequence[str]]] = [
        "uuid",
        "name",
        "description",
        "start_time",
        "end_time",
        "user_triggered",
        "job_status",
        "file_url",
        "message_log",
    ]

    list_display: Sequence[Union[str, Callable]] = [
        "name",
        "start_time",
        "user_triggered",
        "job_status",
    ]

    search_fields: Sequence[str] = [
        "name",
        "description",
        "user_triggered__username",
        "user_triggered__email",
        "user_triggered__first_name",
        "user_triggered__last_name",
    ]

    ordering: Optional[Sequence[str]] = ["-start_time"]

    @display(description=gettext("File Link"))
    def file_url(self, obj: Job) -> SafeText:
        """Return the URL to access the file, or a message if there is no file associated with the
        job.
        """
        if not obj.has_file():
            return mark_safe(gettext("No file attached"))
        return format_html(
            '<a target="_blank" href="{}">{}</a>',
            reverse("recordtransfer:job_file", args=[obj.uuid]),
            obj.attached_file.name,
        )

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this model admin."""
        return bool(obj and request.user.is_superuser)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin for the User model.

    Permissions:
        - add: Allowed by superusers only
        - change: Allowed by superusers only. Staff users can update their user details through the
        Profile page.
        - delete: Allowed by superusers only
    """

    form = UserAdminForm

    fieldsets = (
        *UserAdmin.fieldsets,  # original form fieldsets, expanded
        (
            "Contact Information",
            {
                "fields": (
                    "phone_number",
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "province_or_state",
                    "other_province_or_state",
                    "postal_or_zip_code",
                    "country",
                ),
            },
        ),
        (
            "Email Updates",
            {
                "fields": ("gets_submission_email_updates",),
            },
        ),
    )

    inlines: Sequence[Type[InlineModelAdmin]] = [
        SubmissionInline,
        SubmissionGroupInline,
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Determine whether add permission is granted for this user admin."""
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether change permission is granted for this user admin."""
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Determine whether delete permission is granted for this user admin."""
        return bool(obj and request.user.is_superuser)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: Optional[str] = None,
        form_url: str = "",
        extra_context: Optional[dict] = None,
    ) -> TemplateResponse:
        """Add JS context for contact info form."""
        extra_context = extra_context or {}

        # Create context for JavaScript
        extra_context["js_context"] = {
            # Contact Info Form
            "id_province_or_state": HtmlIds.ID_CONTACT_INFO_PROVINCE_OR_STATE,
            "id_other_province_or_state": HtmlIds.ID_CONTACT_INFO_OTHER_PROVINCE_OR_STATE,
            "other_province_or_state_value": OtherValues.PROVINCE_OR_STATE,
        }

        return super().changeform_view(request, object_id, form_url or "", extra_context)

    @sensitive_post_parameters_m
    def user_change_password(
        self, request: HttpRequest, id: str, form_url: str = ""
    ) -> HttpResponse:
        """Send a notification email when a user's password is changed."""
        response = super().user_change_password(request, id, form_url)
        user = self.get_object(request, unquote(id))
        form = self.change_password_form(user, request.POST)
        if form.is_valid() and request.method == "POST" and user is not None:
            context = {
                "subject": gettext("Password updated"),
                "changed_item": gettext("password"),
                "changed_status": gettext("updated"),
            }
            send_user_account_updated.delay(user, context)
        return response

    def save_model(self, request: HttpRequest, obj: User, form: ModelForm, change: bool) -> None:
        """Enforce superuser permissions checks and send notification emails
        for other account updates.
        """
        if change and obj.is_superuser and not request.user.is_superuser:
            messages.set_level(request, messages.ERROR)
            msg = "Non-superusers cannot modify superuser accounts."
            self.message_user(request, msg, messages.ERROR)
        else:
            super().save_model(request, obj, form, change)
            if change and (
                not obj.is_active
                or "is_superuser" in form.changed_data
                or "is_staff" in form.changed_data
            ):
                if not obj.is_active:
                    context = {
                        "subject": gettext("Account Deactivated"),
                        "changed_item": gettext("account"),
                        "changed_status": gettext("deactivated"),
                    }
                else:
                    context = {
                        "subject": gettext("Account updated"),
                        "changed_item": gettext("account"),
                        "changed_status": gettext("updated"),
                        "changed_list": self._get_changed_message(form.changed_data, obj),
                    }

                send_user_account_updated.delay(obj, context)

    def _get_changed_message(self, changed_data: list, user: User):
        """Generate a list of changed status message for certain account details."""
        message_list = []
        if "is_superuser" in changed_data:
            if user.is_superuser:
                message_list.append(
                    gettext("Superuser privileges have been added to your account.")
                )
            else:
                message_list.append(
                    gettext("Superuser privileges have been removed from your account.")
                )
        if "is_staff" in changed_data:
            if user.is_staff:
                message_list.append(gettext("Staff privileges have been added to your account."))
            else:
                message_list.append(
                    gettext("Staff privileges have been removed from your account.")
                )
        return message_list


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Admin for the SiteSetting model.

    Permissions:
        - add: Not allowed
        - change: Only by superusers
        - delete: Not allowed
    """

    list_display: Sequence[Union[str, Callable]] = ["key", "value_type", "value", "change_date"]
    search_fields: Sequence[str] = ["key", "value"]
    readonly_fields: Sequence[Union[str, Callable]] = [
        "key",
        "value_type",
        "change_date",
        "changed_by",
    ]

    form = SiteSettingModelForm

    change_form_template = "admin/sitesetting_change_form.html"

    def save_model(
        self, request: HttpRequest, obj: SiteSetting, form: ModelForm, change: bool
    ) -> None:
        """Override save_model to set the changed_by field."""
        obj.changed_by = request.user
        super().save_model(request, obj, form, change)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: Optional[str] = None,
        form_url: Optional[str] = "",
        extra_context: Optional[dict] = None,
    ) -> TemplateResponse:
        """Add custom context to the change form and skip validation on reset."""
        extra_context = extra_context or {}
        if object_id:
            obj: Optional[SiteSetting] = self.get_object(request, object_id)
            if obj:
                extra_context["setting_default_value"] = obj.default_value

        # Skip form validation if "_reset" is in POST
        if request.method == "POST" and "_reset" in request.POST:
            if object_id:
                obj = self.get_object(request, object_id)
                if obj:
                    self.reset_to_default(request, obj)
            # Instead of returning HttpResponseRedirect, raise it
            # to ensure TemplateResponse return type
            from django.http import HttpResponseRedirect

            return HttpResponseRedirect(request.get_full_path())

        return super().changeform_view(request, object_id, form_url or "", extra_context)

    def reset_to_default(self, request: HttpRequest, obj: SiteSetting) -> None:
        """Reset the site setting to its default value."""
        try:
            user = User.objects.get(pk=request.user.pk)
            obj.reset_to_default(user)
            messages.success(
                request,
                f'Setting "{obj.key}" has been reset to its default value.',
            )
        except Exception as e:
            messages.error(
                request,
                f'Failed to reset setting "{obj.key}": {e!s}',
            )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent adding new site settings through the admin interface."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        """Allow modification of site settings only by superusers."""
        return request.user.is_superuser

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        """Prevent deletion of site settings through the admin interface."""
        return False
