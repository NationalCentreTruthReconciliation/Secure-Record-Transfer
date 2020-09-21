from io import StringIO, BytesIO
import zipfile
import csv
from pathlib import Path

from django.contrib import admin
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin

from recordtransfer.settings import BAG_STORAGE_FOLDER
from recordtransfer.models import Bag, UploadSession, UploadedFile, User


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

    actions = ['export_selected_bags', 'export_selected_reports', 'mark_not_started',
               'mark_in_progress', 'mark_complete']
    list_display = ['user', 'bagging_date', 'bag_name', 'review_status']
    ordering = ['bagging_date']

    def export_selected_bags(self, request, queryset):
        bag_folder = Path(BAG_STORAGE_FOLDER)

        csv_file = StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(["Username", "Bagging Date", "Bag Location", "Review Status"])

        for bag in queryset:
            writer.writerow(
                [
                    bag.user.username,
                    bag.bagging_date,
                    str(bag_folder / bag.bag_name),
                    bag.get_review_status_display(),
                ]
            )

        csv_file.seek(0)
        response = HttpResponse(csv_file, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=exported-bag-info.csv'
        csv_file.close()
        return response
    export_selected_bags.short_description = 'Export CSV information for selected Bags'

    def export_selected_reports(self, request, queryset):
        zipf = BytesIO()
        zipped_reports = zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False)
        for bag in queryset:
            zipped_reports.writestr(bag.report_name, bag.report_contents)
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

    def response_change(self, request, obj):
        if "_view_report" in request.POST:
            return HttpResponse(obj.report_contents, content_type='text/html')
        return super().response_change(request, obj)


admin.site.register(Bag, BagAdmin)
admin.site.register(UploadedFile, UploadedFileAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UploadSession)
