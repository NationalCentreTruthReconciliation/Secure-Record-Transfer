''' Custom administration code for the admin site '''
import csv
import json
import zipfile
from io import StringIO, BytesIO
from pathlib import Path

from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin, sensitive_post_parameters_m
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from recordtransfer.atom import flatten_meta_tree_atom_style
from recordtransfer.bagger import update_bag
from recordtransfer.caais import flatten_meta_tree
from recordtransfer.forms import BagForm, InlineBagForm, InlineAppraisalForm, SubmissionForm
from recordtransfer.jobs import create_downloadable_bag, send_user_account_updated
from recordtransfer.models import User, UploadSession, UploadedFile, Bag, BagGroup, Appraisal, \
    Submission, Job, Right, SourceType, SourceRole

from bagitobjecttransfer.settings.base import MEDIA_ROOT


def linkify(field_name):
    ''' Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    '''
    def _linkify(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj is None:
            return '-'
        app_label = linked_obj._meta.app_label
        model_name = linked_obj._meta.model_name
        view_name = f'admin:{app_label}_{model_name}_change'
        link_url = reverse(view_name, args=[linked_obj.pk])
        return format_html('<a href="{}">{}</a>', link_url, linked_obj)

    _linkify.short_description = field_name.replace('_', ' ') # Sets column name
    return _linkify


FLATTEN_FUNCTIONS = {
    ('caais', 1, 0): flatten_meta_tree,
    ('atom', 2, 6): lambda b: flatten_meta_tree_atom_style(b, version=(2, 6)),
    ('atom', 2, 3): lambda b: flatten_meta_tree_atom_style(b, version=(2, 3)),
    ('atom', 2, 2): lambda b: flatten_meta_tree_atom_style(b, version=(2, 2)),
    ('atom', 2, 1): lambda b: flatten_meta_tree_atom_style(b, version=(2, 1)),
}
def export_bag_csv(queryset, version: tuple, filename_prefix: str = None):
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
    convert_bag_to_row = FLATTEN_FUNCTIONS[version]
    for i, bag in enumerate(queryset, 0):
        new_row = convert_bag_to_row(bag)
        # Write the headers on the first loop
        if i == 0:
            writer.writerow(new_row.keys())
        writer.writerow(new_row.values())
    csv_file.seek(0)

    response = HttpResponse(csv_file, content_type='text/csv')
    local_time = timezone.localtime(timezone.now()).strftime(r'%Y%m%d_%H%M%S')
    if not filename_prefix:
        filename_prefix = str(version[0]) + '_' + '.'.join(version[1:])
    filename = f"{filename_prefix}{local_time}.csv"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    csv_file.close()
    return response


class ReadOnlyAdmin(admin.ModelAdmin):
    ''' A model admin that does not allow any editing/changing/ or deletions
    '''
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in obj._meta.fields] + \
               [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ''' Admin for the User model.
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

    @staticmethod
    def _get_changed_message(changed_data: list, user: User):
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


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    ''' Admin for the UploadedFile model
    '''
    actions = [
        'clean_temp_files',
    ]

    def clean_temp_files(self, request, queryset):
        ''' Remove temporary files stored on the file system by the uploaded
        files
        '''
        for uploaded_file in queryset:
            uploaded_file.delete_file()
    clean_temp_files.short_description = gettext('Remove temp files on filesystem')


class UploadedFileInline(admin.TabularInline):
    ''' Inline admin for the UploadedFile model. Used to view the files
    associated with an upload session. Deletions are not allowed.
    '''
    model = UploadedFile
    max_num = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = False


@admin.register(UploadSession)
class UploadSessionAdmin(admin.ModelAdmin):
    ''' Admin for the UploadSession model
    '''
    model = UploadSession

    inlines = [
        UploadedFileInline,
    ]

    list_display = [
        'token',
        'started_at',
    ]

    ordering = [
        '-started_at',
    ]


@admin.register(Bag)
class BagAdmin(admin.ModelAdmin):
    ''' Admin for the Bag model. Adds a view to start a job to zip the bag up so
    it can be downloaded. The zip/download view can be accessed at
    code:`submission/<id>/zip/`
    '''
    change_form_template = 'admin/bag_change_form.html'

    form = BagForm

    actions = [
        'export_caais_reports',
        'export_caais_csv',
        'export_atom_2_6_csv',
        'export_atom_2_3_csv',
        'export_atom_2_2_csv',
        'export_atom_2_1_csv',
    ]

    # Display in Admin GUI
    list_display = [
        'bagging_date',
        'bag_name',
        linkify('part_of_group'),
    ]

    ordering = [
        '-bagging_date',
    ]

    def get_urls(self):
        ''' Add zip/ view to admin
        '''
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        download_url = [
            path('<path:object_id>/zip/',
                 self.admin_site.admin_view(self.create_zipped_bag),
                 name='%s_%s_zip' % info),
        ]
        return download_url + urls

    def create_zipped_bag(self, request, object_id):
        ''' Start a background job to create a downloadable bag

        Args:
            request: The originating request
            object_id: The ID for the submission
        '''
        bag = Bag.objects.filter(id=object_id).first()
        if bag:
            create_downloadable_bag.delay(bag, request.user)
            self.message_user(request, mark_safe(gettext(
                'A downloadable bag is being generated. Check the '
                "<a href='/admin/recordtransfer/job'>Jobs</a> page for more information."
            )))
            return HttpResponseRedirect('../')
        # Error response
        msg = gettext('Bag with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
            'key': object_id,
        }
        self.message_user(request, msg, messages.WARNING)
        url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def export_caais_csv(self, request, queryset):
        return export_bag_csv(queryset, ('caais', 1, 0))
    export_caais_csv.short_description = 'Export CAAIS 1.0 CSV for Selected'

    def export_atom_2_6_csv(self, request, queryset):
        return export_bag_csv(queryset, ('atom', 2, 6))
    export_atom_2_6_csv.short_description = 'Export AtoM 2.6 Accession CSV for Selected'

    def export_atom_2_3_csv(self, request, queryset):
        return export_bag_csv(queryset, ('atom', 2, 3))
    export_atom_2_3_csv.short_description = 'Export AtoM 2.3 Accession CSV for Selected'

    def export_atom_2_2_csv(self, request, queryset):
        return export_bag_csv(queryset, ('atom', 2, 2))
    export_atom_2_2_csv.short_description = 'Export AtoM 2.2 Accession CSV for Selected'

    def export_atom_2_1_csv(self, request, queryset):
        return export_bag_csv(queryset, ('atom', 2, 1))
    export_atom_2_1_csv.short_description = 'Export AtoM 2.1 Accession CSV for Selected'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.update_filesystem_bag(request, obj)

    def update_filesystem_bag(self, request, bag: Bag):
        ''' Update the Bag on the filesystem. Messages the user depending on the
        action taken.

        Args:
            request: The originating request
            bag (Bag): The bag that is to be updated
        '''
        bagit_tags = flatten_meta_tree(json.loads(bag.caais_metadata))
        bag_location = bag.location
        results = update_bag(bag_location, bagit_tags)

        if not results['bag_exists']:
            msg = f'The bag at "{bag_location}" was moved or deleted, so it could not be updated!'
            messages.error(request, msg)
        elif not results['bag_valid'] and results['num_fields_updated'] == 0:
            msg = f'The bag at "{bag_location}" was found to be invalid!'
            messages.error(request, msg)
        elif not results['bag_valid'] and results['num_fields_updated'] > 0:
            msg = (f'The bag-info.txt for the bag at "{bag_location}" was updated, but is now '
                   'invalid!')
            messages.error(request, msg)
        elif results['bag_valid'] and results['num_fields_updated'] == 0:
            msg = f'No updates were made to the bag-info.txt for the bag at "{bag_location}"'
            messages.info(request, msg)
        else:
            num_updates = results['num_fields_updated']
            msg = (f'{num_updates} related fields were updated in the bag-info.txt for the bag at '
                   f'"{bag_location}"')
            messages.success(request, msg)


class BagInline(admin.TabularInline):
    ''' Inline admin for the Bag model. Used to view Bags associated with a
    BagGroup. Deletions are not allowed.
    '''
    model = Bag
    max_num = 0
    show_change_link = True
    form = InlineBagForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = False


@admin.register(BagGroup)
class BagGroupAdmin(ReadOnlyAdmin):
    ''' Admin for the BagGroup model. Bags can be viewed in-line.
    '''
    inlines = [
        BagInline,
    ]

    list_display = [
        'name',
        'created_by',
        'bags_in_group',
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

    def bags_in_group(self, obj):
        return len(Bag.objects.filter(part_of_group=obj))
    bags_in_group.short_description = 'Number of Bags in Group'

    def export_caais_csv(self, request, queryset):
        related_bags = Bag.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('caais', 1, 0))
    export_caais_csv.short_description = 'Export CAAIS 1.0 CSV for Bags in Selected'

    def export_atom_2_6_csv(self, request, queryset):
        related_bags = Bag.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 6))
    export_atom_2_6_csv.short_description = 'Export AtoM 2.6 Accession CSV for Bags in Selected'

    def export_atom_2_3_csv(self, request, queryset):
        related_bags = Bag.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 3))
    export_atom_2_3_csv.short_description = 'Export AtoM 2.3 Accession CSV for Bags in Selected'

    def export_atom_2_2_csv(self, request, queryset):
        related_bags = Bag.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 2))
    export_atom_2_2_csv.short_description = 'Export AtoM 2.2 Accession CSV for Bags in Selected'

    def export_atom_2_1_csv(self, request, queryset):
        related_bags = Bag.objects.filter(part_of_group__in=queryset)
        return export_bag_csv(related_bags, ('atom', 2, 1))
    export_atom_2_1_csv.short_description = 'Export AtoM 2.1 Accession CSV for Bags in Selected'


@admin.register(Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    ''' Admin for the Appraisal model
    '''
    list_display = [
        'appraisal_type',
        'appraisal_date',
        linkify('user'),
        linkify('submission'),
    ]

    ordering = [
        '-appraisal_date',
    ]


class AppraisalInline(admin.TabularInline):
    ''' Inline admin for the Appraisal model. Used to edit Appraisals associated
    with a Submission. Deletions are not allowed.
    '''
    model = Appraisal
    max_num = 64
    extra = 0
    show_change_link = True
    form = InlineAppraisalForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    ''' Admin for the Submission model. Adds a view to view the transfer report
    associated with the submission. The report view can be accessed at
    code:`submission/<id>/report/`
    '''
    change_form_template = 'admin/submission_change_form.html'

    form = SubmissionForm

    inlines = [
        AppraisalInline,
    ]

    actions = [
        'export_reports',
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

    def get_form(self, request, obj=None, change=False, **kwargs):
        ''' Add the URL to the Bag's change page to the form
        '''
        _class = super().get_form(request, obj, change, **kwargs)

        class WrappedSubmissionForm(_class):
            def __new__(cls, *args, **kwargs):
                if obj.bag:
                    kwargs['bag_change_url'] = obj.bag.get_admin_change_url()
                return _class(*args, **kwargs)

        return WrappedSubmissionForm


@admin.register(Job)
class JobAdmin(ReadOnlyAdmin):
    ''' Admin for the Job model. Adds a view to download the file associated
    with the job, if there is a file. The file download view can be accessed at
    code:`job/<id>/download/`
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
        if job:
            msg = gettext('Job with ID “%(key)s” doesn’t exist. Perhaps it was deleted?') % {
                'key': object_id,
            }
            self.message_user(request, msg, messages.WARNING)
            url = reverse('admin:index', current_app=self.admin_site.name)
            return HttpResponseRedirect(url)
        if job.attached_file:
            file_path = Path(MEDIA_ROOT) / job.attached_file.name
            file_handle = open(file_path, "rb")
            response = HttpResponse(file_handle, content_type='application/x-zip-compressed')
            response['Content-Disposition'] = f'attachment; filename="{file_path.name}"'
            return response
        # Error response
        msg = gettext('Could not find a file attached to the Job with ID “%(key)s”') % {
            'key': object_id
        }
        self.message_user(request, msg, messages.WARNING)
        return HttpResponseRedirect('../')

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


@admin.register(Right)
@admin.register(SourceType)
@admin.register(SourceRole)
class TaxonomyAdmin(admin.ModelAdmin):
    ''' Admin for a taxonomy model

    Permissions:
        - Add: Allowed
        - change: Allowed
        - delete: Allowed
    '''

    list_display = [
        'name',
        'description',
    ]

    fieldsets = [
        (None, {'fields': ['name', 'description']}),
    ]

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
