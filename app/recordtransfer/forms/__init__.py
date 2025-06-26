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
from recordtransfer.forms.user_forms import (
    SignUpForm,
    UserAccountInfoForm,
    UserContactInfoForm,
)

__all__ = [
    "AcceptLegal",
    "ContactInfoForm",
    "ExtendedRecordDescriptionForm",
    "FinalStepFormNoUpload",
    "GroupSubmissionForm",
    "OtherIdentifiersForm",
    "OtherIdentifiersFormSet",
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
    "UserAccountInfoForm",
    "UserContactInfoForm",
    "clear_form_errors",
]
