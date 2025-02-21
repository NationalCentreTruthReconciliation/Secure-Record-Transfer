from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from . import views

app_name = "recordtransfer"
urlpatterns = [
    path("", views.home.Index.as_view(), name="index"),
    path(
        "transfer/",
        login_required(views.transfer.TransferFormWizard.as_view()),
        name="transfer",
    ),
    path(
        "transfer/error/",
        login_required(views.home.SystemErrorPage.as_view()),
        name="systemerror",
    ),
    path("transfer/sent/", views.transfer.TransferSent.as_view(), name="transfersent"),
    path(
        "transfer/expired/",
        views.transfer.InProgressSubmissionExpired.as_view(),
        name="in_progress_submission_expired",
    ),
    path(
        "inprogress/<uuid:uuid>/delete/",
        login_required(views.transfer.DeleteTransfer.as_view()),
        name="transferdelete",
    ),
    path(
        "inprogress/<uuid:uuid>/delete/confirm/",
        login_required(views.transfer.DeleteTransfer.as_view()),
        name="confirmtransferdelete",
    ),
    path("about/", views.home.About.as_view(), name="about"),
    path("profile/", login_required(views.profile.UserProfile.as_view()), name="userprofile"),
    path(
        "submission/<uuid:uuid>/",
        login_required(views.submission.SubmissionDetail.as_view()),
        name="submissiondetail",
    ),
    path(
        "submission/<uuid:uuid>/csv",
        login_required(views.submission.SubmissionCsv.as_view()),
        name="submissioncsv",
    ),
    path(
        "submission_group/new",
        login_required(views.submission.SubmissionGroupCreateView.as_view()),
        name="submissiongroupnew",
    ),
    path(
        "submission_group/<uuid:uuid>/",
        login_required(views.submission.SubmissionGroupDetailView.as_view()),
        name="submissiongroupdetail",
    ),
    path(
        "user/<int:user_id>/submission_groups/",
        login_required(views.submission.get_user_submission_groups),
        name="get_user_submission_groups",
    ),
]

if settings.DEBUG:
    # Serve media files directly without nginx in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Check permissions and serve through nginx in production
    urlpatterns.append(
        re_path(r"media/(?P<path>.*)", login_required(views.media.media_request), name="media")
    )

if settings.TESTING or settings.FILE_UPLOAD_ENABLED:
    urlpatterns.extend(
        [
            path(
                "upload-session/",
                login_required(views.media.create_upload_session),
                name="create_upload_session",
            ),
            path(
                "upload-session/<session_token>/files/",
                login_required(views.media.upload_or_list_files),
                name="upload_files",
            ),
            path(
                "upload-session/<session_token>/files/<file_name>/",
                login_required(views.media.uploaded_file),
                name="uploaded_file",
            ),
        ]
    )

if settings.TESTING or settings.SIGN_UP_ENABLED:
    urlpatterns.extend(
        [
            path(
                "createaccount/",
                views.account.CreateAccount.as_view(),
                name="createaccount",
            ),
            path(
                "createaccount/sent/",
                views.account.ActivationSent.as_view(),
                name="activationsent",
            ),
            path(
                "createaccount/complete/",
                views.account.ActivationComplete.as_view(),
                name="accountcreated",
            ),
            path(
                "createaccount/invalid/",
                views.account.ActivationInvalid.as_view(),
                name="activationinvalid",
            ),
            re_path(
                (
                    "createaccount/"
                    "activate/"
                    r"(?P<uidb64>[0-9A-Za-z_\-]+)/"
                    r"(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$"
                ),
                views.account.activate_account,
                name="activateaccount",
            ),
        ]
    )
