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
from recordtransfer.atom import flatten_meta_tree_atom_style


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
        help_text=gettext('Saving any change to this field will log a new event in the Caais '
                          'metadata'),
    )

    level_of_detail = forms.ChoiceField(
        choices = [(c, c) for c in [
            'Not Specified',
            'Minimal',
            'Partial',
            'Full',
        ]],
        required=False,
        widget=forms.Select(),
        label=gettext('Level of detail'),
        help_text=gettext('Saving any change to this field will log a new event in the Caais '
                          'metadata'),
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

            accession_id = self._bag_metadata['section_1']['accession_identifier']
            self.fields['accession_identifier'].initial = accession_id
            level_of_detail = self._bag_metadata['section_7']['level_of_detail']
            self.fields['level_of_detail'].initial = level_of_detail or 'Not Specified'

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
        caais_metadata_changed = False

        new_accession_id = cleaned_data['accession_identifier']
        curr_accession_id = self._bag_metadata['section_1']['accession_identifier']
        if curr_accession_id != new_accession_id and new_accession_id:
            if not curr_accession_id or \
                (curr_accession_id == DEFAULT_DATA['section_1'].get('accession_identifier')):
                note = f'Accession ID was set to "{new_accession_id}"'
                self.log_new_event('Accession ID Assigned', note)
            else:
                note = f'Accession ID Changed from "{curr_accession_id}" to "{new_accession_id}"'
                self.log_new_event('Accession ID Modified', note)
            self._bag_metadata['section_1']['accession_identifier'] = new_accession_id
            caais_metadata_changed = True

        appraisal_value = cleaned_data['appraisal_statement_value']
        if appraisal_value:
            appraisal = OrderedDict()
            appraisal_type = cleaned_data['appraisal_statement_type']
            appraisal_note = cleaned_data['appraisal_statement_note']
            appraisal['appraisal_statement_type'] = appraisal_type
            appraisal['appraisal_statement_value'] = appraisal_value
            appraisal['appraisal_statement_note'] = appraisal_note
            self.log_new_event(f'{appraisal_type} Added')
            self._bag_metadata['section_4']['appraisal_statement'].append(appraisal)
            caais_metadata_changed = True

        level_of_detail = cleaned_data['level_of_detail']
        curr_level_of_detail = self._bag_metadata['section_7']['level_of_detail']
        if curr_level_of_detail != level_of_detail and level_of_detail and \
            level_of_detail != 'Not Specified':
            if not curr_level_of_detail or \
                (curr_level_of_detail == DEFAULT_DATA['section_7'].get('level_of_detail')):
                note = f'Level of Detail was set to {level_of_detail}'
                self.log_new_event('Level of Detail Assigned', note)
            else:
                note = f'Level of Detail Changed from {curr_level_of_detail} to {level_of_detail}'
                self.log_new_event('Level of Detail Changed', note)
            self._bag_metadata['section_7']['level_of_detail'] = level_of_detail
            caais_metadata_changed = True

        if caais_metadata_changed:
            cleaned_data['caais_metadata'] = json.dumps(self._bag_metadata)

        return cleaned_data


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
