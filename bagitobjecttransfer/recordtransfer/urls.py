from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.urls import path, re_path

import bagitobjecttransfer.settings.base

from . import forms, views
from . import settings as recordtransfersettings

# Set up transfer forms depending on whether file uploads are enabled or disabled
if recordtransfersettings.FILE_UPLOAD_ENABLED:
    _transfer_forms = [
        ("acceptlegal", forms.AcceptLegal),
        ("contactinfo", forms.ContactInfoForm),
        ("sourceinfo", forms.SourceInfoForm),
        ("recorddescription", forms.RecordDescriptionForm),
        ("rights", formset_factory(forms.RightsForm, formset=forms.RightsFormSet, extra=1)),
        ("otheridentifiers", formset_factory(forms.OtherIdentifiersForm, extra=1)),
        ("grouptransfer", forms.GroupTransferForm),
        ("uploadfiles", forms.UploadFilesForm),
    ]
else:
    _transfer_forms = [
        ("acceptlegal", forms.AcceptLegal),
        ("contactinfo", forms.ContactInfoForm),
        ("sourceinfo", forms.SourceInfoForm),
        ("recorddescription", forms.ExtendedRecordDescriptionForm),  # Different
        ("rights", formset_factory(forms.RightsForm, formset=forms.RightsFormSet, extra=1)),
        ("otheridentifiers", formset_factory(forms.OtherIdentifiersForm, extra=1)),
        ("grouptransfer", forms.GroupTransferForm),
        ("finalnotes", forms.FinalStepFormNoUpload),  # Different
    ]

app_name = "recordtransfer"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path(
        "transfer/",
        login_required(views.TransferFormWizard.as_view(_transfer_forms)),
        name="transfer",
    ),
    path("transfer/error/", login_required(views.SystemErrorPage.as_view()), name="systemerror"),
    path("transfer/sent/", views.TransferSent.as_view(), name="transfersent"),
    path(
        "inprogress/<uuid:uuid>/delete/",
        login_required(views.DeleteTransfer.as_view()),
        name="transferdelete",
    ),
    path(
        "inprogress/<uuid:uuid>/delete/confirm/",
        login_required(views.DeleteTransfer.as_view()),
        name="confirmtransferdelete",
    ),
    path("about/", views.About.as_view(), name="about"),
    path("profile/", login_required(views.UserProfile.as_view()), name="userprofile"),
    path(
        "submission/<uuid:uuid>/",
        login_required(views.SubmissionDetail.as_view()),
        name="submissiondetail",
    ),
    path(
        "submission/<uuid:uuid>/csv",
        login_required(views.SubmissionCsv.as_view()),
        name="submissioncsv",
    ),
    path(
        "submission_group/new",
        login_required(views.SubmissionGroupCreateView.as_view()),
        name="submissiongroupnew",
    ),
    path(
        "submission_group/<uuid:uuid>/",
        login_required(views.SubmissionGroupDetailView.as_view()),
        name="submissiongroupdetail",
    ),
    path(
        "user/<int:user_id>/submission_groups/",
        login_required(views.get_user_submission_groups),
        name="get_user_submission_groups",
    ),
]

if settings.TESTING or not settings.DEBUG:
    urlpatterns.append(
        re_path(r"media/(?P<path>.*)", login_required(views.media_request), name="media")
    )

if settings.TESTING or recordtransfersettings.FILE_UPLOAD_ENABLED:
    urlpatterns.extend(
        [
            path("transfer/checkfile/", login_required(views.accept_file), name="checkfile"),
            path("transfer/uploadfile/", login_required(views.uploadfiles), name="uploadfile"),
        ]
    )

if settings.TESTING or bagitobjecttransfer.settings.base.SIGN_UP_ENABLED:
    urlpatterns.extend(
        [
            path("createaccount/", views.CreateAccount.as_view(), name="createaccount"),
            path("createaccount/sent/", views.ActivationSent.as_view(), name="activationsent"),
            path(
                "createaccount/complete/",
                views.ActivationComplete.as_view(),
                name="accountcreated",
            ),
            path(
                "createaccount/invalid/",
                views.ActivationInvalid.as_view(),
                name="activationinvalid",
            ),
            re_path(
                (
                    "createaccount/"
                    "activate/"
                    r"(?P<uidb64>[0-9A-Za-z_\-]+)/"
                    r"(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$"
                ),
                views.activate_account,
                name="activateaccount",
            ),
        ]
    )
