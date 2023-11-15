''' Forms specific to the recordtransfer admin site '''
from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext

from recordtransfer.models import SubmissionGroup, Submission, UploadSession, UploadedFile, User


class RecordTransferModelForm(forms.ModelForm):
    ''' Adds disabled_fields to forms.ModelForm
    '''

    disabled_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and self.disabled_fields:
            # Disable fields
            for field in self.disabled_fields:
                if field in self.fields:
                    self.fields[field].disabled = True


class UploadedFileForm(RecordTransferModelForm):
    class Meta:
        model = UploadedFile
        fields = (
            'name',
            'session',
            'file_upload'
        )

    exists = forms.BooleanField()


class InlineUploadedFileForm(RecordTransferModelForm):
    class Meta:
        model = UploadedFile
        fields = (
            'name',
        )

    exists = forms.BooleanField()


class UploadSessionForm(RecordTransferModelForm):
    ''' For for vieweing UploadSessions. This form should not be used to provide edit
    capabilities in-line for UploadSessions.
    '''

    class Meta:
        model = UploadSession
        fields = (
            'token',
            'started_at'
        )

    number_of_files_uploaded = forms.IntegerField(required=False)


class SubmissionForm(RecordTransferModelForm):
    ''' Form for editing Submissions.
    '''

    class Meta:
        model = Submission
        fields = (
            'submission_date',
            'metadata',
            'user',
            'upload_session',
            'part_of_group',
            'uuid',
        )

    disabled_fields = ['submission_date', 'metadata', 'upload_session', 'user', 'part_of_group', 'uuid']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, 'instance') and self.instance.metadata:
            # TODO: This makes the tiny link by the Metadata title in the Submission form.
            self.fields['metadata'].help_text = ' | '.join([
                format_html('<a href="{}">{}</a>', url, gettext(text)) for url, text in [
                    (self.instance.get_admin_metadata_change_url(), 'View or Change Metadata'),
                ]
            ])
        self.fields['metadata'].widget.can_add_related = False


class InlineSubmissionForm(RecordTransferModelForm):
    ''' Form for viewing Submissions in-line. This form should not be used to provide edit
    capabilities in-line for Submissions.
    '''
    class Meta:
        model = Submission
        fields = (
            'submission_date',
            'metadata',
            'review_status',
            'part_of_group',
        )


class InlineSubmissionGroupForm(RecordTransferModelForm):
    ''' Form used to view SubmissionGroups in-line. This form should not be used to provide edit
    capabilities in-line for a SubmissionGroup.
    '''

    class Meta:
        model = SubmissionGroup
        fields = (
            'name',
            'description',
        )

    number_of_submissions_in_group = forms.IntegerField(required=False)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'gets_notification_emails',
        )

    gets_notification_emails = forms.CheckboxInput()
