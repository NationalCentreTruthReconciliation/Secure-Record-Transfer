"""Provides all forms used in the Record Transfer application."""

from recordtransfer.forms.admin_forms import SubmissionModelForm
from recordtransfer.forms.submission_forms import (
    AcceptLegal,
    ContactInfoForm,
    ExtendedRecordDescriptionForm,
    FinalStepFormNoUpload,
    GroupSubmissionForm,
    OtherIdentifiersForm,
    OtherIdentifiersFormSet,
    RecordDescriptionForm,
    ReviewForm,
    RightsForm,
    RightsFormSet,
    SourceInfoForm,
    SubmissionForm,
    UploadFilesForm,
    clear_form_errors,
)
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.forms.user_forms import ProfileContactInfoForm, SignUpForm, UserProfileForm

__all__ = [
    "AcceptLegal",
    "ContactInfoForm",
    "ExtendedRecordDescriptionForm",
    "FinalStepFormNoUpload",
    "GroupSubmissionForm",
    "OtherIdentifiersForm",
    "OtherIdentifiersFormSet",
    "ProfileContactInfoForm",
    "RecordDescriptionForm",
    "ReviewForm",
    "RightsForm",
    "RightsFormSet",
    "SignUpForm",
    "SourceInfoForm",
    "SubmissionForm",
    "SubmissionGroupForm",
    "SubmissionModelForm",
    "UploadFilesForm",
    "UserProfileForm",
    "clear_form_errors",
]
