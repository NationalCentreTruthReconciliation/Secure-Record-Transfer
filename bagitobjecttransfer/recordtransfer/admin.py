import json
import zipfile
import csv
from io import StringIO, BytesIO
from pathlib import Path
from collections import OrderedDict

from django import forms
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import gettext
from django.contrib.auth.admin import UserAdmin
from django.template.loader import render_to_string

from recordtransfer.settings import BAG_STORAGE_FOLDER, DEFAULT_DATA
from recordtransfer.models import Bag, UploadSession, UploadedFile, User
from recordtransfer.caais import flatten_meta_tree


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


class BagForm(forms.ModelForm):
    accession_identifier = forms.CharField(
        max_length=128,
        min_length=2,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': gettext('Update Accession ID')
        }),
        label=gettext('Accession identifier'),
        help_text=gettext('Any change to this field will log a new event in the Caais metadata')
    )

    appraisal_statement_type = forms.ChoiceField(
        choices = [(c, c) for c in [
            'Archival Appraisal',
            'Monetary Appraisal',
        ]],
        required=False,
        widget=forms.Select(),
        label=gettext('New Appraisal Type'),
    )

    appraisal_statement_value = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Record a new appraisal statement here.'),
        }),
        label=gettext('New Appraisal Statement'),
        help_text=gettext('Leave empty if you do not want to add an appraisal statement'),
    )

    appraisal_statement_note = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.Textarea(attrs={
            'rows': '6',
            'placeholder': gettext('Record any notes about the appraisal statement here '
                                   '(optional).'),
        }),
        label=gettext('Notes About Appraisal Statement'),
        help_text=gettext('Leave empty if you do not want to add an appraisal statement'),
    )

    disabled_fields = ['bagging_date', 'bag_name', 'caais_metadata', 'user']

    class Meta:
        model = Bag
        fields = (
            'bagging_date',
            'bag_name',
            'caais_metadata',
            'user',
            'review_status',
        )

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Disable fields
            for field in self.disabled_fields:
                self.fields[field].disabled = True
            self.fields['caais_metadata'].help_text = gettext('Click View Metadata as HTML below '
                                                              'for a human-readable report')
            # Load string metadata as object
            self._bag_metadata = json.loads(instance.caais_metadata)
            # Populate Accession ID in form
            accession_id = self._bag_metadata['section_1']['accession_identifier']
            self.fields['accession_identifier'].initial = accession_id

    def log_new_event(self, event_type: str, event_note: str = ''):
        new_event = OrderedDict()
        new_event['event_type'] = event_type
        new_event['event_date'] = timezone.now().strftime(r'%Y-%m-%d %H:%M:%S %Z')
        if self.current_user:
            new_event['event_agent'] = (f'User {self.current_user.username} '
                                        f'({self.current_user.email})')
        else:
            new_event['event_agent'] = 'Transfer Portal User'
        new_event['event_note'] = event_note
        self._bag_metadata['section_5']['event_statement'].append(new_event)

    def clean(self):
        cleaned_data = super().clean()

        new_accession_id = cleaned_data['accession_identifier']
        curr_accession_id = self._bag_metadata['section_1']['accession_identifier']
        caais_metadata_changed = False
        if curr_accession_id != new_accession_id and new_accession_id:
            if not curr_accession_id or \
                (curr_accession_id == DEFAULT_DATA['section_1'].get('accession_identifier')):
                self.log_new_event(
                    'Access ID Assigned',
                    f'Accession ID was set to "{new_accession_id}"')
            else:
                self.log_new_event(
                    'Accession ID Modified',
                    f'Accession ID changed from "{curr_accession_id}" to "{new_accession_id}"')
            self._bag_metadata['section_1']['accession_identifier'] = new_accession_id
            caais_metadata_changed = True

        appraisal_value = cleaned_data['appraisal_statement_value']
        if appraisal_value:
            appraisal = OrderedDict()
            appraisal_type = cleaned_data['appraisal_statement_type']
            appraisal_note = cleaned_data['appraisal_statement_note'] or 'NULL'
            appraisal['appraisal_statement_type'] = appraisal_type
            appraisal['appraisal_statement_value'] = appraisal_value
            appraisal['appraisal_statement_note'] = appraisal_note

            self.log_new_event(f'{appraisal_type} Added')
            self._bag_metadata['section_4']['appraisal_statement'].append(appraisal)
            caais_metadata_changed = True

        if caais_metadata_changed:
            cleaned_data['caais_metadata'] = json.dumps(self._bag_metadata)

        return cleaned_data


class BagAdmin(admin.ModelAdmin):
    change_form_template = 'admin/bag_change_form.html'

    form = BagForm

    actions = [
        'export_caais_csv',
        'export_caais_reports',
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
        csv_file = StringIO()
        writer = csv.writer(csv_file)

        for i, bag in enumerate(queryset, 0):
            bag_metadata = json.loads(bag.caais_metadata)
            metadata_as_csv = flatten_meta_tree(bag_metadata)

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
                    str(self.bag_container / bag.user.username / bag.bag_name),
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
    export_caais_csv.short_description = 'Export CAAIS v1.0 CSV data for selected Bags'

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
    export_caais_reports.short_description = 'Export CAAIS v1.0 HTML reports for selected Bags'

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

    def locate_bag(self, bag: Bag):
        return str(self.bag_container / bag.user.username / bag.bag_name)

    def response_change(self, request, obj):
        if "_view_report" in request.POST:
            return HttpResponse(self.render_html_report(obj), content_type='text/html')
        if "_get_bag_location" in request.POST:
            self.message_user(request, f'This bag is located at: {self.locate_bag(obj)}')
            return HttpResponseRedirect('../')
        return super().response_change(request, obj)


admin.site.register(Bag, BagAdmin)
admin.site.register(UploadedFile, UploadedFileAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UploadSession)
