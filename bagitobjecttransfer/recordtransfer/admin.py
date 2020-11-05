import json
import zipfile
import csv
from io import StringIO, BytesIO
from pathlib import Path
from collections import OrderedDict

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import gettext
from django.contrib.auth.admin import UserAdmin
from django.template.loader import render_to_string

from recordtransfer.settings import BAG_STORAGE_FOLDER
from recordtransfer.models import *
from recordtransfer.caais import flatten_meta_tree
from recordtransfer.atom import flatten_meta_tree_atom_style
from recordtransfer.bagger import update_bag
from recordtransfer.forms import BagForm


class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in obj._meta.fields] + \
               [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CustomUserAdmin(UserAdmin):
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


class UploadedFileAdmin(admin.ModelAdmin):
    actions = ['clean_temp_files']

    def clean_temp_files(self, request, queryset):
        for uploaded_file in queryset:
            uploaded_file.delete_file()
    clean_temp_files.short_description = 'Remove temp files on filesystem'


class BagAdmin(admin.ModelAdmin):
    change_form_template = 'admin/bag_change_form.html'

    form = BagForm

    actions = [
        'export_caais_reports',
        'export_caais_csv',
        'export_atom_2_6_csv',
        'export_atom_2_3_csv',
        'export_atom_2_2_csv',
        'export_atom_2_1_csv',
        'mark_not_started',
        'mark_in_progress',
        'mark_complete'
    ]

    # Display in Admin GUI
    list_display = ['user', 'bagging_date', 'bag_name', 'review_status']
    ordering = ['bagging_date']

    def __init__(self, t, obj):
        super().__init__(t, obj)
        self.bag_container = Path(BAG_STORAGE_FOLDER)

    def get_form(self, request, obj=None, change=False, **kwargs):
        _class = super().get_form(request, obj, change, **kwargs)

        class UserBagForm(_class):
            def __new__(cls, *args, **kwargs):
                ''' Add current user when the form is created '''
                kwargs['current_user'] = request.user
                return _class(*args, **kwargs)

        return UserBagForm

    def export_caais_csv(self, request, queryset):
        def convert_bag_to_row(bag):
            new_row = OrderedDict()
            new_row['Username'] = bag.user.username
            new_row['Bagging Date'] = bag.bagging_date
            new_row['Bag Location'] = str(self.bag_container / bag.user.username / bag.bag_name)
            new_row['Review Status'] = bag.get_review_status_display()
            bag_metadata = json.loads(bag.caais_metadata)
            metadata_as_csv = flatten_meta_tree(bag_metadata)
            new_row.update(metadata_as_csv)
            return new_row
        return self.export_generic_csv(queryset, convert_bag_to_row, 'caais_v1.0_')
    export_caais_csv.short_description = 'Export CAAIS 1.0 CSV for Selected'

    def export_atom_2_6_csv(self, request, queryset):
        def convert_bag_to_row(bag):
            bag_metadata = json.loads(bag.caais_metadata)
            return flatten_meta_tree_atom_style(bag_metadata, version=(2, 6))
        return self.export_generic_csv(queryset, convert_bag_to_row, 'atom_2.6_')
    export_atom_2_6_csv.short_description = 'Export AtoM 2.6 Accession CSV for Selected'

    def export_atom_2_3_csv(self, request, queryset):
        def convert_bag_to_row(bag):
            bag_metadata = json.loads(bag.caais_metadata)
            return flatten_meta_tree_atom_style(bag_metadata, version=(2, 3))
        return self.export_generic_csv(queryset, convert_bag_to_row, 'atom_2.3_')
    export_atom_2_3_csv.short_description = 'Export AtoM 2.3 Accession CSV for Selected'

    def export_atom_2_2_csv(self, request, queryset):
        def convert_bag_to_row(bag):
            bag_metadata = json.loads(bag.caais_metadata)
            return flatten_meta_tree_atom_style(bag_metadata, version=(2, 2))
        return self.export_generic_csv(queryset, convert_bag_to_row, 'atom_2.2_')
    export_atom_2_2_csv.short_description = 'Export AtoM 2.2 Accession CSV for Selected'

    def export_atom_2_1_csv(self, request, queryset):
        def convert_bag_to_row(bag):
            bag_metadata = json.loads(bag.caais_metadata)
            return flatten_meta_tree_atom_style(bag_metadata, version=(2, 1))
        return self.export_generic_csv(queryset, convert_bag_to_row, 'atom_2.1_')
    export_atom_2_1_csv.short_description = 'Export AtoM 2.1 Accession CSV for Selected'

    def export_generic_csv(self, queryset, convert_bag_to_row, filename_prefix: str):
        csv_file = StringIO()
        writer = csv.writer(csv_file)

        for i, bag in enumerate(queryset, 0):
            new_row = convert_bag_to_row(bag)
            # Write the headers on the first loop
            if i == 0:
                writer.writerow(new_row.keys())
            writer.writerow(new_row.values())

        csv_file.seek(0)
        response = HttpResponse(csv_file, content_type='text/csv')
        local_time = timezone.localtime(timezone.now()).strftime(r'%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}{local_time}.csv"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        csv_file.close()
        return response

    def export_caais_reports(self, request, queryset):
        zipf = BytesIO()
        zipped_reports = zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False)
        for bag in queryset:
            report = self.render_html_report(bag)
            zipped_reports.writestr(f'{bag.bag_name}.html', report)
        zipped_reports.close()
        zipf.seek(0)
        response = HttpResponse(zipf, content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename=exported-bag-reports.zip'
        zipf.close()
        return response
    export_caais_reports.short_description = 'Export CAAIS 1.0 HTML reports for Selected'

    def mark_not_started(self, request, queryset):
        queryset.update(review_status=Bag.ReviewStatus.NOT_REVIEWED)
    # pylint: disable=no-member
    mark_not_started.short_description = f'Mark bags as "{Bag.ReviewStatus.NOT_REVIEWED.label}"'

    def mark_in_progress(self, request, queryset):
        queryset.update(review_status=Bag.ReviewStatus.REVIEW_STARTED)
    # pylint: disable=no-member
    mark_in_progress.short_description = f'Mark bags as "{Bag.ReviewStatus.REVIEW_STARTED.label}"'

    def mark_complete(self, request, queryset):
        queryset.update(review_status=Bag.ReviewStatus.REVIEW_COMPLETE)
    # pylint: disable=no-member
    mark_complete.short_description = f'Mark bags as "{Bag.ReviewStatus.REVIEW_COMPLETE.label}"'

    def render_html_report(self, bag: Bag):
        return render_to_string('recordtransfer/report/metadata_report.html', context={
            'bag': bag,
            'current_date': timezone.now(),
            'metadata': json.loads(bag.caais_metadata),
        })

    def locate_bag(self, bag: Bag):
        return str(self.bag_container / bag.user.username / bag.bag_name)

    def save_model(self, request, obj, form, change):
        if '_view_report' not in request.POST and '_get_bag_location' not in request.POST:
            super().save_model(request, obj, form, change)
            self.update_filesystem_bag(request, obj)

    def update_filesystem_bag(self, request, bag: Bag):
        bagit_tags = flatten_meta_tree(json.loads(bag.caais_metadata))
        bag_location = self.locate_bag(bag)
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
            msg = (f'{num_updates} fields were updated in the bag-info.txt for the bag at '
                   f'"{bag_location}"')
            messages.success(request, msg)

    def response_change(self, request, obj):
        if "_view_report" in request.POST:
            return HttpResponse(self.render_html_report(obj), content_type='text/html')
        if "_get_bag_location" in request.POST:
            self.message_user(request, f'This bag is located at: {self.locate_bag(obj)}')
            return HttpResponseRedirect('../')
        return super().response_change(request, obj)


class JobAdmin(ReadOnlyAdmin):
    list_display = ('name', 'start_time', 'user_triggered', 'job_status', 'attached_file')

    def attached_file(self, obj):
        if obj.attached_file:
            return f"<a href='{obj.attached_file.url}'>{gettext('Download')}</a>"
        return gettext("No attachment")
    attached_file.allow_tags = True
    attached_file.short_description = 'Download Attachment'


admin.site.register(Bag, BagAdmin)
admin.site.register(UploadedFile, UploadedFileAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UploadSession)
admin.site.register(Job, JobAdmin)
