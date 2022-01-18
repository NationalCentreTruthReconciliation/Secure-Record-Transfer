''' Forms specific to the recordtransfer admin site '''
from django import forms
from django.utils.translation import gettext

from recordtransfer.models import Appraisal, Bag, BagGroup, Submission, UploadSession


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
            'accession_identifier',
            'review_status',
            'level_of_detail',
        )

    disabled_fields = ['submission_date', 'bag', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['accession_identifier'].required = False
        if hasattr(self, 'instance'):
            self.fields['bag'].help_text = gettext(
                '<a href="{0}">Click to view bag</a>'
            ).format(self.instance.bag.get_admin_change_url())
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


class BagForm(RecordTransferModelForm):
    ''' Form for vieweing Bags in the admin. This form should not be used to provide edit
    capabilities for a Bag.
    '''

    class Meta:
        model = Bag
        fields = (
            'uuid',
            'user',
            'bagging_date',
            'bag_name',
            'caais_metadata',
            'part_of_group',
            'upload_session',
        )

    disabled_fields = [
        'uuid',
        'user',
        'bagging_date',
        'bag_name',
        'caais_metadata',
        'part_of_group',
        'location',
        'exists',
    ]

    title = forms.CharField(required=False)
    location = forms.CharField(required=False)
    exists = forms.BooleanField(required=False)

    '''
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
    '''


class InlineBagForm(RecordTransferModelForm):
    ''' Form used to view Bags in-line. This form should not be used to provide edit capabilities
    in-line for a Bag.
    '''

    class Meta:
        model = Bag
        fields = (
            'bag_name',
            'bagging_date',
        )

    title = forms.CharField(required=False)


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