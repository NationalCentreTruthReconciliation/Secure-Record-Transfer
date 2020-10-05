import json
import zipfile
import csv
from io import StringIO, BytesIO
from pathlib import Path

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin
from django.template.loader import render_to_string

from recordtransfer.settings import BAG_STORAGE_FOLDER
from recordtransfer.models import Bag, UploadSession, UploadedFile, User
from recordtransfer.caais import convert_meta_tree_to_csv_row


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

    actions = [
        'export_selected_bags',
        'export_selected_reports',
        'mark_not_started',
        'mark_in_progress',
        'mark_complete'
    ]

    # Display in Admin GUI
    list_display = ['user', 'bagging_date', 'bag_name', 'review_status']
    ordering = ['bagging_date']

    def export_selected_bags(self, request, queryset):
        bag_folder = Path(BAG_STORAGE_FOLDER)

        csv_file = StringIO()
        writer = csv.writer(csv_file)

        for i, bag in enumerate(queryset, 0):
            bag_metadata = json.loads(bag.caais_metadata)
            metadata_as_csv = convert_meta_tree_to_csv_row(bag_metadata)

            # Write the headers on the first loop
            if i == 0:
                writer.writerow([
                    'Username',
                    'Bagging Date',
                    'Bag Location',
                    'Review Status',
                    *metadata_as_csv.keys(),
                ])

            writer.writerow(
                [
                    bag.user.username,
                    bag.bagging_date,
                    str(bag_folder / bag.user.username / bag.bag_name),
                    bag.get_review_status_display(),
                    *metadata_as_csv.values(),
                ]
            )

        csv_file.seek(0)
        response = HttpResponse(csv_file, content_type='text/csv')
        local_time = timezone.localtime(timezone.now()).strftime(r'%Y%m%d_%H%M%S')
        filename = f"exported_bag_info_{local_time}.csv"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        csv_file.close()
        return response
    export_selected_bags.short_description = 'Export CSV information for selected Bags'

    def export_selected_reports(self, request, queryset):
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
    export_selected_reports.short_description = 'Export HTML reports for selected Bags'

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
            'user': bag.user,
            'metadata': json.loads(bag.caais_metadata),
        })

    def response_change(self, request, obj):
        if "_view_report" in request.POST:
            return HttpResponse(self.render_html_report(obj), content_type='text/html')
        return super().response_change(request, obj)


admin.site.register(Bag, BagAdmin)
admin.site.register(UploadedFile, UploadedFileAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UploadSession)
