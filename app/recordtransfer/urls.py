from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from . import views

app_name = "recordtransfer"
urlpatterns = [
    path("", views.home.Index.as_view(), name="index"),
    path(
        "submission/<uuid:resume>/<uuid:group>/",
        login_required(views.pre_submission.SubmissionFormWizard.as_view()),
        name="resume_submit_with_group",
    ),
    path(
        "submission/<uuid:resume>/",
        login_required(views.pre_submission.SubmissionFormWizard.as_view()),
        name="resume_submit",
    ),
    path(
        "submission/<uuid:group>/",
        login_required(views.pre_submission.SubmissionFormWizard.as_view()),
        name="submit_with_group",
    ),
    path(
        "submission/<uuid:uuid>/csv/",
        login_required(views.post_submission.SubmissionCsv.as_view()),
        name="submission_csv",
    ),
    path(
        "submission/<uuid:uuid>/",
        login_required(views.post_submission.SubmissionDetail.as_view()),
        name="submission_detail",
    ),
    path(
        "submission/",
        login_required(views.pre_submission.SubmissionFormWizard.as_view()),
        name="submit",
    ),
    path(
        "error/",
        login_required(views.home.SystemErrorPage.as_view()),
        name="system_error",
    ),
    path("submission/sent/", views.pre_submission.SubmissionSent.as_view(), name="submission_sent"),
    path(
        "submission/in-progress/expired/",
        views.pre_submission.InProgressSubmissionExpired.as_view(),
        name="in_progress_submission_expired",
    ),
    path(
        "submission/in-progress/<uuid:uuid>/",
        login_required(views.pre_submission.DeleteInProgressSubmission.as_view()),
        name="delete_in_progress",
    ),
    path("about/", views.home.About.as_view(), name="about"),
    path("user/profile/", login_required(views.profile.UserProfile.as_view()), name="user_profile"),
    path(
        "submission-group/",
        login_required(views.post_submission.SubmissionGroupCreateView.as_view()),
        name="submission_group_new",
    ),
    path(
        "submission-group/<uuid:uuid>/",
        login_required(views.post_submission.SubmissionGroupDetailView.as_view()),
        name="submission_group_detail",
    ),
    path(
        "user/<int:user_id>/submission-group/",
        login_required(views.post_submission.get_user_submission_groups),
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
                "account/",
                views.account.CreateAccount.as_view(),
                name="create_account",
            ),
            path(
                "account/activation/sent/",
                views.account.ActivationSent.as_view(),
                name="activation_sent",
            ),
            path(
                "account/activation/complete/",
                views.account.ActivationComplete.as_view(),
                name="account_created",
            ),
            path(
                "account/activation/invalid/",
                views.account.ActivationInvalid.as_view(),
            ),
            re_path(
                (
                    "account/activation/"
                    r"(?P<uidb64>[0-9A-Za-z_\-]+)/"
                    r"(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$"
                ),
                views.account.activate_account,
                name="activate_account",
            ),
        ]
    )
