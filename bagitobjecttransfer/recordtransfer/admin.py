from io import StringIO
import csv

from django.contrib import admin
from django.http import HttpResponse

from recordtransfer.models import Bag, UploadSession, UploadedFile


class BagAdmin(admin.ModelAdmin):
    actions = ['export_selected_bags']
    list_display = ['user', 'bagging_date', 'bag_location']
    ordering = ['bagging_date']

    def export_selected_bags(self, request, queryset):
        string_file = StringIO()

        writer = csv.writer(string_file)
        writer.writerow(
            [
                "Username",
                "Bagging Date",
                "Bag Location",
                "Report Location"
            ]
        )

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

    export_selected_bags.short_description = 'Export CSV information for selected Bags'


admin.site.register(Bag, BagAdmin)
admin.site.register(UploadedFile)
admin.site.register(UploadSession)
