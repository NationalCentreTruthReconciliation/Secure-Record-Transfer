''' Custom administration code for the admin site '''
import csv
import logging
import os
import zipfile
from io import StringIO, BytesIO
from pathlib import Path

from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin, sensitive_post_parameters_m
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from caais.export import ExportVersion
from recordtransfer.forms import InlineBagGroupForm, SubmissionForm, \
    InlineSubmissionForm, AppraisalForm, InlineAppraisalFormSet, UploadSessionForm, \
    UploadedFileForm, InlineUploadedFileForm
from recordtransfer.jobs import create_downloadable_bag, send_user_account_updated
from recordtransfer.models import User, UploadSession, UploadedFile, BagGroup, Appraisal, \
    Submission, Job
from recordtransfer.settings import ALLOW_BAG_CHANGES

from bagitobjecttransfer.settings.base import MEDIA_ROOT


LOGGER = logging.getLogger(__name__)


def linkify(field_name):
    ''' Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    '''
    def _linkify(obj):
        try:
            linked_obj = getattr(obj, field_name)
            if not linked_obj:
                return '-'

            app_label = linked_obj._meta.app_label
            model_name = linked_obj._meta.model_name
            view_name = f'admin:{app_label}_{model_name}_change'
            link_url = reverse(view_name, args=[linked_obj.pk])
            return format_html('<a href="{}">{}</a>', link_url, linked_obj)

        except AttributeError:
            return '-'

    _linkify.short_description = field_name.replace('_', ' ') # Sets column name
    return _linkify


def export_bag_csv(queryset, version: ExportVersion, filename_prefix: str = None):
    ''' Export one or more bags to a CSV file

    Args:
        queryset: The set of one or more bags
        version: The version of CSV to export
        filename_prefix: The prefix of the file to create. If none specifed, one
            is created

    Returns:
        HttpResponse: A text/csv response to download the CSV file
    '''
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    for i, submission in enumerate(queryset, 0):
        new_row = submission.bag.flatten(version)
        new_row.update(submission.appraisals.flatten(version))
        # Write the headers on the first loop
        if i == 0:
            writer.writerow(new_row.keys())
        writer.writerow(new_row.values())
    csv_file.seek(0)

    response = HttpResponse(csv_file, content_type='text/csv')
    local_time = timezone.localtime(timezone.now()).strftime(r'%Y%m%d_%H%M%S')
    if not filename_prefix:
        version_bits = str(version).split('_')
        filename_prefix = '{0}_v{1}_'.format(version_bits[0], '.'.join([str(x) for x in version_bits[1:]]))
    filename = f"{filename_prefix}{local_time}.csv"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    csv_file.close()
    return response


class ReadOnlyAdmin(admin.ModelAdmin):
    ''' A model admin that does not allow any editing/changing/ or deletions

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in obj._meta.fields] + \
               [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UploadedFile)
class UploadedFileAdmin(ReadOnlyAdmin):
    ''' Admin for the UploadedFile model

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    class Media:
        js = ("recordtransfer/js/hideMediaLink.js",)

    change_form_template = 'admin/readonly_change_form.html'

    form = UploadedFileForm

    actions = [
        'clean_temp_files',
    ]

    list_display = [
        'name',
        'exists',
        linkify('session'),
    ]

    ordering = [
        '-session',
        'name'
    ]

    def clean_temp_files(self, request, queryset):
        ''' Remove temporary files stored on the file system by the uploaded
        files
        '''
        for uploaded_file in queryset:
            uploaded_file.remove()
    clean_temp_files.short_description = gettext('Remove temp files on filesystem')


class UploadedFileInline(admin.TabularInline):
    ''' Inline admin for the UploadedFile model. Used to view the files
    associated with an upload session

    Permission:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    form = InlineUploadedFileForm
    model = UploadedFile
    max_num = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UploadSession)
class UploadSessionAdmin(ReadOnlyAdmin):
    ''' Admin for the UploadSession model

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Not allowed
    '''
    change_form_template = 'admin/readonly_change_form.html'

    form = UploadSessionForm

    inlines = [
        UploadedFileInline,
    ]

    list_display = [
        'token',
        'started_at',
        'number_of_files_uploaded'
    ]

    ordering = [
        '-started_at',
    ]


@admin.register(BagGroup)
class BagGroupAdmin(ReadOnlyAdmin):
    ''' Admin for the BagGroup model. Bags can be viewed in-line.

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only by superusers
    '''

    list_display = [
        'name',
        linkify('created_by'),
        'number_of_bags_in_group',
    ]

    search_fields = [
        'name',
        'uuid',
    ]

    ordering = [
        '-created_by',
    ]

    actions = [
        'export_caais_csv',
        'export_atom_2_6_csv',
        'export_atom_2_3_csv',
        'export_atom_2_2_csv',
        'export_atom_2_1_csv',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    def export_caais_csv(self, request, queryset):
        related_bags = Submission.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('caais', 1, 0))
    export_caais_csv.short_description = 'Export CAAIS 1.0 CSV for Bags in Selected'

    def export_atom_2_6_csv(self, request, queryset):
        related_bags = Submission.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 6))
    export_atom_2_6_csv.short_description = 'Export AtoM 2.6 Accession CSV for Bags in Selected'

    def export_atom_2_3_csv(self, request, queryset):
        related_bags = Submission.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 3))
    export_atom_2_3_csv.short_description = 'Export AtoM 2.3 Accession CSV for Bags in Selected'

    def export_atom_2_2_csv(self, request, queryset):
        related_bags = Submission.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 2))
    export_atom_2_2_csv.short_description = 'Export AtoM 2.2 Accession CSV for Bags in Selected'

    def export_atom_2_1_csv(self, request, queryset):
        related_bags = Submission.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 1))
    export_atom_2_1_csv.short_description = 'Export AtoM 2.1 Accession CSV for Bags in Selected'


class BagGroupInline(admin.TabularInline):
    ''' Inline admin for the Appraisal model. Used to edit Appraisals associated
    with a Submission. Deletions are not allowed.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to BagGroup page for change ability
        - delete: Not allowed - go to BagGroup page for delete ability
    '''
    model = BagGroup
    max_num = 0
    show_change_link = True

    form = InlineBagGroupForm

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    ''' Admin for the Appraisal model

    Permissions:
        - add: Not allowed (must be done from the Appraisal inline)
        - change: Allowed if editor created the appraisal
        - delete: Allowed if editor created the appraisal, or if editor is a superuser
    '''
    form = AppraisalForm

    actions = [
        'delete_selected'
    ]

    list_display = [
        'appraisal_type',
        'appraisal_date',
        linkify('user'),
        linkify('submission'),
    ]

    ordering = [
        '-appraisal_date',
    ]

    readonly_fields = [
        'user',
        'appraisal_date'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj and request.user == obj.user

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or (obj and request.user == obj.user)

    def delete_queryset(self, request, queryset):
        ''' Delete the Appraisals from the Appraisals' Submissions' Bags (if Bag
        editing is allowed)
        '''
        # Find appraisals in queryset with a bag and sort them by bag ID
        appraisals_with_bags = queryset\
            .filter(~Q(submission=None))\
            .filter(~Q(submission__bag=None))\
            .order_by('submission__bag__id')

        # save and update each Bag only once
        if appraisals_with_bags and ALLOW_BAG_CHANGES:
            prev_bag = None
            for appraisal in appraisals_with_bags:
                curr_bag = appraisal.submission.bag
                curr_bag.remove_appraisal(request.user, appraisal, commit=True)
                prev_bag = curr_bag

        elif appraisals_with_bags:
            messages.warning(request, gettext(
                'One or more appraisals were deleted, an operation that would normally have '
                "affected the Bags associated with the appraisals' submissions', but "
                'ALLOW_BAG_CHANGES is OFF, so no changes were made to the Bag(s)'
            ))

        super().delete_queryset(request, queryset)


class AppraisalInline(admin.TabularInline):
    ''' Inline admin for the Appraisal model. Used to edit Appraisals associated
    with a Submission. Deletions are not allowed.

    Permissions:
        - add: Allowed
        - change: Not allowed - go to Appraisal page for change ability
        - delete: Not allowed - go to Appraisal page for delete ability
    '''
    model = Appraisal
    max_num = 64
    extra = 0
    show_change_link = True

    form = AppraisalForm
    formset = InlineAppraisalFormSet

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = False

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    ''' Admin for the Submission model. Adds a view to view the transfer report
    associated with the submission. The report view can be accessed at
    code:`submission/<id>/report/`

    Permissions:
        - add: Not allowed
        - change: Allowed
        - delete: Only by superusers
    '''
    change_form_template = 'admin/submission_change_form.html'

    form = SubmissionForm

    inlines = [
        AppraisalInline,
    ]

    actions = [
        'export_caais_reports',
        'export_caais_csv',
        'export_atom_2_6_csv',
        'export_atom_2_3_csv',
        'export_atom_2_2_csv',
        'export_atom_2_1_csv',
        'export_reports',
    ]

    search_fields = [
        'id',
        'bag__accession_title',
    ]

    list_display = [
        'submission_date',
        'id',
        'review_status',
        linkify('user'),
        linkify('bag'),
    ]

    ordering = [
        '-submission_date',
    ]

    readonly_fields = [
        'submission_date',
        'user',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    def get_urls(self):
        ''' Add report/ view to admin
        '''
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        report_url = [
            path('<path:object_id>/report/',
                 self.admin_site.admin_view(self.view_report),
                 name='%s_%s_report' % info),
        ]
        return report_url + urls

    def view_report(self, request, object_id):
        ''' Redirect to the submission's report if the submission exists

        Args:
            request: The originating request
            object_id: The ID for the submission
        '''
        submission = Submission.objects.filter(id=object_id).first()
        if submission:
            return HttpResponse(submission.get_report())
        # Error response
        msg = gettext('Submission with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def export_reports(self, request, queryset):
        ''' Download an application/x-zip-compressed file containing reports
        for each of the selected submissions.

        Args:
            request: The originating request
            queryset: One or more submissions
        '''
        zipf = BytesIO()
        with zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False) as zipped_reports:
            for submission in queryset:
                if submission and submission.bag:
                    report = submission.get_report()
                    zipped_reports.writestr(f'{submission.bag.bag_name}.html', report)
        zipf.seek(0)
        response = HttpResponse(zipf, content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename=exported-bag-reports.zip'
        zipf.close()
        return response
    export_reports.short_description = 'Export CAAIS submission reports for Selected'

    def save_related(self, request, form, formsets, change):
        ''' Update Bag in case an Appraisal is added. Deleting inline Appraisals
        is not allowed, so the case of deleting from the formset is not handled.
        '''
        for formset in formsets:
            if formset.model != Appraisal:
                continue

            obj = form.instance
            appraisals = formset.save(commit=False)

            if not appraisals:
                continue

            for appraisal in appraisals:
                appraisal.user = request.user
                appraisal.save()
                if ALLOW_BAG_CHANGES:
                    pass

            if ALLOW_BAG_CHANGES:
                obj.save()
            else:
                messages.warning(request, gettext(
                    'A change to the appraisals was made to this submission that would normally '
                    "have affected the Bag's bag-info.txt, but ALLOW_BAG_CHANGES is OFF, so no "
                    'change was made to the Bag'
                ))

            formset.save_m2m()
        super().save_related(request, form, formsets, change)

    def save_model(self, request, obj, form, change):
        ''' Update Bag in case the accession identifier or level of detail
        changes.
        '''
        bag_changes = change and any(
            f in form.changed_data for f in ('accession_identifier', 'level_of_detail')
        )

        if not bag_changes:
            super().save_model(request, obj, form, change)
            return

        if not ALLOW_BAG_CHANGES:
            messages.warning(request, gettext(
                "A change was made to this submission that would have affected the Bag's "
                'bag-info.txt, but ALLOW_BAG_CHANGES is OFF, so no change was made to the Bag'
            ))
            super().save_model(request, obj, form, change)
            return

        if 'accession_identifier' in form.changed_data:
            updated_id = form.cleaned_data['accession_identifier']
            obj.bag.update_accession_id(updated_id, commit=False)

        if 'level_of_detail' in form.changed_data:
            # TODO: Not sure what this LevelOfDetail function is for?
            updated_choice = Submission.LevelOfDetail(form.cleaned_data['level_of_detail'])
            obj.bag.update_level_of_detail(request.user, str(updated_choice.label), commit=False)

        obj.bag.save()
        super().save_model(request, obj, form, change)

    def create_zipped_bag(self, request, object_id):
        ''' Start a background job to create a downloadable bag

        Args:
            request: The originating request
            object_id: The ID for the submission
        '''
        bag = Submission.objects.filter(id=object_id).first()
        if bag and not os.path.exists(bag.location):
            create_downloadable_bag.delay(bag, request.user)
            self.message_user(request, mark_safe(gettext(
                'A downloadable bag is being generated. Check the '
                "<a href='/admin/recordtransfer/job'>Jobs</a> page for more information."
            )))
            return HttpResponseRedirect('../')
        if bag:
            self.message_user(request, (
                'A downloadable bag could not be generated, the bag at {0} may have been moved or '
                'deleted.'.format(bag.location)
            ), messages.WARNING)
            return HttpResponseRedirect('../')
        # Error response
        msg = gettext('Bag with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def export_caais_csv(self, request, queryset):
        return export_bag_csv(queryset, ExportVersion.CAAIS_1_0)

    export_caais_csv.short_description = 'Export CAAIS 1.0 CSV for Selected'

    def export_atom_2_6_csv(self, request, queryset):
        return export_bag_csv(queryset, ExportVersion.ATOM_2_6)

    export_atom_2_6_csv.short_description = 'Export AtoM 2.6 Accession CSV for Selected'

    def export_atom_2_3_csv(self, request, queryset):
        return export_bag_csv(queryset, ExportVersion.ATOM_2_3)

    export_atom_2_3_csv.short_description = 'Export AtoM 2.3 Accession CSV for Selected'

    def export_atom_2_2_csv(self, request, queryset):
        return export_bag_csv(queryset, ExportVersion.ATOM_2_2)

    export_atom_2_2_csv.short_description = 'Export AtoM 2.2 Accession CSV for Selected'

    def export_atom_2_1_csv(self, request, queryset):
        return export_bag_csv(queryset, ExportVersion.ATOM_2_1)

    export_atom_2_1_csv.short_description = 'Export AtoM 2.1 Accession CSV for Selected'


class SubmissionInline(admin.TabularInline):
    ''' Inline admin for the Appraisal model. Used to edit Appraisals associated
    with a Submission. Deletions are not allowed.

    Permissions:
        - add: Not allowed
        - change: Not allowed - go to Submission page for change ability
        - delete: Only by superusers
    '''
    model = Submission
    max_num = 0
    show_change_link = True
    form = InlineSubmissionForm

    ordering = ['-submission_date']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser


@admin.register(Job)
class JobAdmin(ReadOnlyAdmin):
    ''' Admin for the Job model. Adds a view to download the file associated
    with the job, if there is a file. The file download view can be accessed at
    code:`job/<id>/download/`

    Permissions:
        - add: Not allowed
        - change: Not allowed
        - delete: Only if current user created job
    '''
    change_form_template = 'admin/job_change_form.html'

    list_display = [
        'name',
        'start_time',
        'user_triggered',
        'job_status',
    ]

    ordering = [
        '-start_time'
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return obj and request.user == obj.user_triggered

    def get_urls(self):
        ''' Add download/ view to admin
        '''
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        report_url = [
            path('<path:object_id>/download/',
                 self.admin_site.admin_view(self.download_file),
                 name='%s_%s_download' % info),
        ]
        return report_url + urls

    def download_file(self, request, object_id):
        ''' Download an application/x-zip-compressed file for the job, if the
        file and the job exist

        Args:
            request: The originating request
            object_id: The ID for the job
        '''
        job = Job.objects.filter(id=object_id).first()
        if job and job.attached_file:
            file_path = Path(MEDIA_ROOT) / job.attached_file.name
            file_handle = open(file_path, "rb")
            response = HttpResponse(file_handle, content_type='application/x-zip-compressed')
            response['Content-Disposition'] = f'attachment; filename="{file_path.name}"'
            return response
        if job:
            msg = gettext('Could not find a file attached to the Job with ID “%(key)s”') % {
                'key': object_id
            }
            self.message_user(request, msg, messages.WARNING)
            return HttpResponseRedirect('../')
        # Error response
        msg = gettext('Job with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def get_fields(self, request, obj=None):
        ''' Hide the attached file field, the user is not allowed to interact
        directly with it. If a user wants this file, they should use the
        download/ view.
        '''
        fields = list(super().get_fields(request, obj))
        exclude_set = set()
        if obj:
            exclude_set.add('attached_file')
        return [f for f in fields if f not in exclude_set]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ''' Admin for the User model.

    Permissions:
        - change: Allowed if editing own account, or if editor is a superuser
        - delete: Allowed by superusers
    '''
    fieldsets = (
        *UserAdmin.fieldsets, # original form fieldsets, expanded
        (                     # New fieldset added on to the bottom
            'Email Updates',  # Group heading of your choice. set to None for a blank space
            {
                'fields': (
                    'gets_bag_email_updates',
                ),
            },
        ),
    )

    inlines = [
        SubmissionInline,
        BagGroupInline,
    ]

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return obj and (request.user.is_superuser or obj == request.user)

    def has_delete_permission(self, request, obj=None):
        return obj and request.user.is_superuser

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=''):
        """ Send a notification email when a user's password is changed. """
        response = super().user_change_password(request, id, form_url)
        user = self.get_object(request, unquote(id))
        form = self.change_password_form(user, request.POST)
        if form.is_valid() and request.method == 'POST':
            context = {
                'subject': gettext("Password updated"),
                'changed_item': gettext("password"),
                'changed_status': gettext("updated")
            }
            send_user_account_updated.delay(user, context)
        return response

    def save_model(self, request, obj, form, change):
        ''' Enforce superuser permissions checks and send notification emails
        for other account updates
        '''
        if change and obj.is_superuser and not request.user.is_superuser:
            messages.set_level(request, messages.ERROR)
            msg = 'Non-superusers cannot modify superuser accounts.'
            self.message_user(request, msg, messages.ERROR)
        else:
            super().save_model(request, obj, form, change)
            if change and (not obj.is_active or "is_superuser" in form.changed_data or \
                           "is_staff" in form.changed_data):
                if not obj.is_active:
                    context = {
                        'subject': gettext("Account Deactivated"),
                        'changed_item': gettext("account"),
                        'changed_status': gettext("deactivated")
                    }
                else:
                    context = {
                        'subject': gettext("Account updated"),
                        'changed_item': gettext("account"),
                        'changed_status': gettext("updated"),
                        'changed_list': self._get_changed_message(form.changed_data, obj)
                    }

                send_user_account_updated.delay(obj, context)

    def _get_changed_message(self, changed_data: list, user: User):
        """ Generate a list of changed status message for certain account details. """
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
                message_list.append(
                    gettext("Staff privileges have been added to your account.")
                )
            else:
                message_list.append(
                    gettext("Staff privileges have been removed from your account.")
                )
        return message_list
