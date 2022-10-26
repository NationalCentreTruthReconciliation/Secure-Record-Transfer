''' Forms specific to the recordtransfer admin site '''
from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext

from recordtransfer.models import Appraisal, BagGroup, Submission, UploadSession, UploadedFile, User
from recordtransfer.settings import ALLOW_BAG_CHANGES


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


class InlineAppraisalFormSet(forms.models.BaseInlineFormSet):
    ''' Formset for inline Appraisal editing. Sets the initial user for the form based on the
    current logged in user.
    '''

    model = Appraisal
    request = None

    @property
    def empty_form(self):
        form = super().empty_form
        if 'user' in form.fields:
            form.initial['user'] = self.request.user
            # form.fields['user'].initial = self.request.user
        return form


class AppraisalForm(RecordTransferModelForm):
    ''' Form for editing Appraisals. Hides the user select field using display:none, as this field
    should be set automatically by whatever controls this form. Adds submission help_text if the
    submission field exists (i.e., if the appraisal is not being edited in-line).
    '''

    class Meta:
        model = Appraisal
        fields = (
            'appraisal_type',
            'statement',
            'note',
            'submission',
            'user',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'note' in self.fields:
            self.fields['note'].required = False

        if 'user' in self.fields:
            self.fields['user'].required = False
            self.fields['user'].widget.can_add_related = False
            self.fields['user'].widget.can_change_related = False
            self.fields['user'].widget.attrs['style'] = 'display:none'

        if hasattr(self, 'instance') and hasattr(self.instance, 'submission') and \
           'submission' in self.fields:
            self.fields['submission'].help_text = gettext(
                '<a href="{0}">Click to view submission</a>'
            ).format(self.instance.submission.get_admin_change_url())


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
    ''' Form for editing Submissions. Adds a help_text to the bag with a link to the bag, if the
    bag exists.
    '''

    class Meta:
        model = Submission
        fields = (
            'submission_date',
            'bag',
            'user',
            'review_status'
        )

    disabled_fields = ['submission_date', 'bag', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, 'instance') and self.instance.bag:
            self.fields['bag'].help_text = ' | '.join([
                format_html('<a href="{}">{}</a>', url, gettext(text)) for url, text in [
                    (self.instance.get_admin_report_url(), 'View Bag metadata'),
                ]
            ])

        self.fields['bag'].widget.can_add_related = False


class InlineSubmissionForm(RecordTransferModelForm):
    ''' Form for viewing Submissions in-line. This form should not be used to provide edit
    capabilities in-line for Submissions.
    '''
    class Meta:
        model = Submission
        fields = (
            'submission_date',
            'bag',
            'review_status',
        )


class InlineBagGroupForm(RecordTransferModelForm):
    ''' Form used to view BagGroups in-line. This form should not be used to provide edit
    capabilities in-line for a BagGroup.
    '''

    class Meta:
        model = BagGroup
        fields = (
            'name',
            'description',
        )

    number_of_bags_in_group = forms.IntegerField(required=False)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'gets_notification_emails',
        )

    gets_notification_emails = forms.CheckboxInput()
