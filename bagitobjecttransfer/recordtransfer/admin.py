"""Custom administration code for the admin site."""

import logging
from pathlib import Path
from typing import Callable

from caais.export import ExportVersion
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin, sensitive_post_parameters_m
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from recordtransfer.emails import send_user_account_updated
from recordtransfer.forms import (
    InlineSubmissionForm,
    InlineSubmissionGroupForm,
    InlineUploadedFileForm,
    SubmissionForm,
    UploadSessionForm,
)
from recordtransfer.jobs import create_downloadable_bag
from recordtransfer.models import (
    Job,
    PermUploadedFile,
    Submission,
    SubmissionGroup,
    TempUploadedFile,
    UploadSession,
    User,
)

LOGGER = logging.getLogger("recordtransfer")


def linkify(field_name: str) -> Callable:
    """Convert a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """

    def _linkify(obj):
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

    _linkify.short_description = field_name.replace("_", " ")  # Sets column name
    return _linkify


@receiver(pre_delete, sender=Job)
def job_file_delete(sender: Job, instance: Job, **kwargs) -> None:
    """FileFields are not deleted automatically after Django 1.11, instead this receiver does it."""
    instance.attached_file.delete(False)


class ReadOnlyAdmin(admin.ModelAdmin):
    """A model admin that does not allow any editing/changing/ or deletions.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return (
            list(self.readonly_fields)
            + [field.name for field in obj._meta.fields]
            + [field.name for field in obj._meta.many_to_many]
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TempUploadedFile)
class TempUploadedFileAdmin(ReadOnlyAdmin):
    """Admin for the UploadedFile model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    class Media:
        js = ("admin_uploadedfile.bundle.js",)

    actions = [
        "clean_temp_files",
    ]

    list_display = [
        "name",
        "exists",
        linkify("session"),
    ]

    ordering = ["-session", "name"]

    @admin.action(description=gettext("Remove temp files on filesystem"))
    def clean_temp_files(self, request, queryset):
        """Remove temporary files stored on the file system by the temporary uploaded
        files.
        """
        for temp_file in queryset:
            temp_file.remove()


@admin.register(PermUploadedFile)
class PermUploadedFileAdmin(ReadOnlyAdmin):
    """Admin for the UploadedFile model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    class Media:
        js = ("admin_uploadedfile.bundle.js",)

    list_display = [
        "name",
        "exists",
        linkify("session"),
    ]

    ordering = ["-session", "name"]


class ReadOnlyInline(admin.TabularInline):
    """Inline admin that does not allow any editing/changing/ or deletions.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    max_num = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TempUploadedFileInline(ReadOnlyInline):
    """Inline admin for the BaseUploadedFile model. Used to view the files
    associated with an upload session.

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    form = InlineUploadedFileForm
    model = TempUploadedFile


class PermUploadedFileInline(ReadOnlyInline):
    """Inline admin for the BaseUploadedFile model. Used to view the files
    associated with an upload session.

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    form = InlineUploadedFileForm
    model = PermUploadedFile


@admin.register(UploadSession)
class UploadSessionAdmin(ReadOnlyAdmin):
    """Admin for the UploadSession model.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    """

    form = UploadSessionForm

    inlines = [
        TempUploadedFileInline,
        PermUploadedFileInline,
    ]

    list_display = ["token", linkify("user"), "started_at", "file_count", "status"]

    ordering = [
        "-started_at",
    ]


class SubmissionInline(ReadOnlyInline):
    """Inline admin for the Submission model.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to Submission page for change ability
        - delete: Only by superusers
    """

    model = Submission
    form = InlineSubmissionForm

    ordering = ["-submission_date"]

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser


@admin.register(SubmissionGroup)
class SubmissionGroupAdmin(ReadOnlyAdmin):
    """Admin for the SubmissionGroup model. Submissions can be viewed in-line.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only by superusers
    """

    list_display = [
        "name",
        linkify("created_by"),
        "number_of_submissions_in_group",
    ]

    inlines = [SubmissionInline]

    search_fields = [
        "name",
        "uuid",
    ]

    ordering = [
        "-created_by",
    ]

    actions = [
        "export_caais_csv",
        "export_atom_2_6_csv",
        "export_atom_2_3_csv",
        "export_atom_2_2_csv",
        "export_atom_2_1_csv",
    ]

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    @admin.action(description=gettext("Export CAAIS 1.0 CSV for Submissions in Selected"))
    def export_caais_csv(self, request, queryset):
        related_submissions = Submission.objects.filter(part_of_group__in=queryset)
        return related_submissions.export_csv(version=ExportVersion.CAAIS_1_0)

    @admin.action(description=gettext("Export AtoM 2.6 Accession CSV for Submissions in Selected"))
    def export_atom_2_6_csv(self, request, queryset):
        related_submissions = Submission.objects.filter(part_of_group__in=queryset)
        return related_submissions.export_csv(version=ExportVersion.ATOM_2_6)

    @admin.action(description=gettext("Export AtoM 2.3 Accession CSV for Submissions in Selected"))
    def export_atom_2_3_csv(self, request, queryset):
        related_submissions = Submission.objects.filter(part_of_group__in=queryset)
        return related_submissions.export_csv(version=ExportVersion.ATOM_2_3)

    @admin.action(description=gettext("Export AtoM 2.2 Accession CSV for Submissions in Selected"))
    def export_atom_2_2_csv(self, request, queryset):
        related_submissions = Submission.objects.filter(part_of_group__in=queryset)
        return related_submissions.export_csv(version=ExportVersion.ATOM_2_2)

    @admin.action(description=gettext("Export AtoM 2.1 Accession CSV for Submissions in Selected"))
    def export_atom_2_1_csv(self, request, queryset):
        related_submissions = Submission.objects.filter(part_of_group__in=queryset)
        return related_submissions.export_csv(version=ExportVersion.ATOM_2_1)


class SubmissionGroupInline(ReadOnlyInline):
    """Inline admin for viewing submission groups.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to SubmissionGroup page for change ability
        - delete: Not allowed - go to SubmissionGroup page for delete ability
    """

    model = SubmissionGroup
    form = InlineSubmissionGroupForm


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin for the Submission model.

    Permissions:
        - add: Not allowed
        - change: Allowed
        - delete: Only by superusers
    """

    change_form_template = "admin/submission_change_form.html"

    form = SubmissionForm

    actions = [
        "export_caais_csv",
        "export_atom_2_6_csv",
        "export_atom_2_3_csv",
        "export_atom_2_2_csv",
        "export_atom_2_1_csv",
    ]

    search_fields = [
        "uuid",
        "metadata__accession_title",
        "user__username",
        "user__email",
    ]

    list_display = [
        "submission_date",
        "uuid",
        "file_count",
        linkify("metadata"),
        linkify("user"),
    ]

    ordering = [
        "-submission_date",
    ]

    readonly_fields = [
        "submission_date",
        "user",
        "upload_session",
        "part_of_group",
        "uuid",
    ]

    def file_count(self, obj):
        if not obj.upload_session:
            return 0
        return obj.upload_session.file_count

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    def get_urls(self):
        """Add extra views to admin."""
        return [
            path(
                "<path:object_id>/zip/",
                self.admin_site.admin_view(self.create_zipped_bag),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_zip",
            ),
        ] + super().get_urls()

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        job = (
            Job.objects.get_queryset()
            .filter(Q(user_triggered=request.user) & Q(submission_id=object_id))
            .first()
        )
        if extra_context is None:
            extra_context = {}
        extra_context["has_generated_bag"] = job is not None
        if job is not None:
            extra_context["generated_bag_url"] = job.get_admin_download_url()
        return super().changeform_view(request, object_id, form_url, extra_context)

    def create_zipped_bag(self, request, object_id) -> HttpResponseRedirect:
        """Start a background job to create a downloadable bag.

        Args:
            request: The originating request
            object_id: The ID for the submission
        """
        submission = Submission.objects.filter(id=object_id).first()

        if submission and submission.upload_session:
            create_downloadable_bag.delay(submission, request.user)

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

    @admin.action(description=gettext("Export CAAIS 1.0 CSV for Selected"))
    def export_caais_csv(self, request, queryset):
        return queryset.export_csv(version=ExportVersion.CAAIS_1_0)

    @admin.action(description=gettext("Export AtoM 2.6 Accession CSV for Selected"))
    def export_atom_2_6_csv(self, request, queryset):
        return queryset.export_csv(version=ExportVersion.ATOM_2_6)

    @admin.action(description=gettext("Export AtoM 2.3 Accession CSV for Selected"))
    def export_atom_2_3_csv(self, request, queryset):
        return queryset.export_csv(version=ExportVersion.ATOM_2_3)

    @admin.action(description=gettext("Export AtoM 2.2 Accession CSV for Selected"))
    def export_atom_2_2_csv(self, request, queryset):
        return queryset.export_csv(version=ExportVersion.ATOM_2_2)

    @admin.action(description=gettext("Export AtoM 2.1 Accession CSV for Selected"))
    def export_atom_2_1_csv(self, request, queryset):
        return queryset.export_csv(version=ExportVersion.ATOM_2_1)


@admin.register(Job)
class JobAdmin(ReadOnlyAdmin):
    """Admin for the Job model. Adds a view to download the file associated
    with the job, if there is a file. The file download view can be accessed at
    code:`job/<id>/download/`.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only if current user created job
    """

    change_form_template = "admin/job_change_form.html"

    list_display = [
        "name",
        "start_time",
        "user_triggered",
        "job_status",
    ]

    ordering = ["-start_time"]

    def has_delete_permission(self, request, obj=None):
        return obj and (request.user == obj.user_triggered or request.user.is_superuser)

    def get_urls(self):
        """Add download/ view to admin"""
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        report_url = [
            path(
                "<path:object_id>/download/",
                self.admin_site.admin_view(self.download_file),
                name="%s_%s_download" % info,
            ),
        ]
        return report_url + urls

    def download_file(self, request, object_id):
        """Download an application/x-zip-compressed file for the job, if the
        file and the job exist

        Args:
            request: The originating request
            object_id: The ID for the job
        """
        job = Job.objects.filter(id=object_id).first()
        if job and job.attached_file:
            file_path = Path(settings.MEDIA_ROOT) / job.attached_file.name
            file_handle = open(file_path, "rb")
            response = HttpResponse(file_handle, content_type="application/x-zip-compressed")
            response["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
            return response
        if job:
            msg = gettext("Could not find a file attached to the Job with ID “%(key)s”") % {
                "key": object_id
            }
            self.message_user(request, msg, messages.WARNING)
            return HttpResponseRedirect("../")
        # Error response
        msg = gettext("Job with ID “%(key)s” doesn’t exist. Perhaps it was deleted?") % {
            "key": object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse("admin:index", current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def get_fields(self, request, obj=None):
        """Hide the attached file field, the user is not allowed to interact
        directly with it. If a user wants this file, they should use the
        download/ view.
        """
        fields = list(super().get_fields(request, obj))
        exclude_set = set()
        if obj:
            exclude_set.add("attached_file")
        return [f for f in fields if f not in exclude_set]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin for the User model.

    Permissions:
        - change: Allowed if editing own account, or if editor is a superuser
        - delete: Allowed by superusers
    """

    fieldsets = (
        *UserAdmin.fieldsets,  # original form fieldsets, expanded
        (  # New fieldset added on to the bottom
            "Email Updates",  # Group heading of your choice. set to None for a blank space
            {
                "fields": ("gets_submission_email_updates",),
            },
        ),
    )

    inlines = [
        SubmissionInline,
        SubmissionGroupInline,
    ]

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj and (request.user.is_superuser or obj == request.user)

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=""):
        """Send a notification email when a user's password is changed."""
        response = super().user_change_password(request, id, form_url)
        user = self.get_object(request, unquote(id))
        form = self.change_password_form(user, request.POST)
        if form.is_valid() and request.method == "POST":
            context = {
                "subject": gettext("Password updated"),
                "changed_item": gettext("password"),
                "changed_status": gettext("updated"),
            }
            send_user_account_updated.delay(user, context)
        return response

    def save_model(self, request, obj, form, change):
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
