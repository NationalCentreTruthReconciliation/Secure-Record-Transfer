from io import StringIO
import csv

from django.contrib import admin
from django.http import HttpResponse

from recordtransfer.models import Bag, UploadSession, UploadedFile


class BagAdmin(admin.ModelAdmin):
    actions = ['export_selected_bags', 'mark_not_started', 'mark_in_progress', 'mark_complete']
    list_display = ['user', 'bagging_date', 'bag_location', 'review_status']
    ordering = ['bagging_date']

    def export_selected_bags(self, request, queryset):
        string_file = StringIO()

        writer = csv.writer(string_file)
        writer.writerow(["Username", "Bagging Date", "Bag Location", "Report Location"])

        for bag in queryset:
            writer.writerow(
                [
                    bag.user.username,
                    bag.bagging_date,
                    bag.bag_location,
                    bag.report_location,
                ]
            )

        string_file.seek(0)
        response = HttpResponse(string_file, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=exported-bag-info.csv'
        return response

    def mark_not_started(self, request, queryset):
        queryset.update(review_status=Bag.ReviewStatus.NOT_REVIEWED)

    def mark_in_progress(self, request, queryset):
        queryset.update(review_status=Bag.ReviewStatus.REVIEW_STARTED)

    def mark_complete(self, request, queryset):
        queryset.update(review_status=Bag.ReviewStatus.REVIEW_COMPLETE)

    export_selected_bags.short_description = 'Export CSV information for selected Bags'

    # pylint: disable=no-member
    mark_not_started.short_description = f'Mark bags as "{Bag.ReviewStatus.NOT_REVIEWED.label}"'
    mark_in_progress.short_description = f'Mark bags as "{Bag.ReviewStatus.REVIEW_STARTED.label}"'
    mark_complete.short_description = f'Mark bags as "{Bag.ReviewStatus.REVIEW_COMPLETE.label}"'



admin.site.register(Bag, BagAdmin)
admin.site.register(UploadedFile)
admin.site.register(UploadSession)
