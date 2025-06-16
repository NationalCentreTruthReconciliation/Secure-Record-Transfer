from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from . import views

app_name = "recordtransfer"
urlpatterns = [
    path("", views.home.Index.as_view(), name="index"),
    path(
        "submission/<uuid:uuid>/csv/",
        login_required(views.post_submission.SubmissionCsvView.as_view()),
        name="submission_csv",
    ),
    path(
        "submission/<uuid:uuid>/",
        login_required(views.post_submission.SubmissionDetailView.as_view()),
        name="submission_detail",
    ),
    path(
        "submission/",
        login_required(views.pre_submission.SubmissionFormWizard.as_view()),
        name="submit",
    ),
    path(
        "error/",
        views.home.SystemErrorPage.as_view(),
        name="system_error",
    ),
    path(
        "submission/sent/", views.pre_submission.SubmissionSent.as_view(), name="submission_sent"
    ),
    path(
        "submission/in-progress/expired/",
        views.pre_submission.InProgressSubmissionExpired.as_view(),
        name="in_progress_submission_expired",
    ),
    path(
        "submission/in-progress/<uuid:uuid>/",
        login_required(views.profile.delete_in_progress_submission),
        name="delete_in_progress_submission_modal",
    ),
    path("about/", views.home.About.as_view(), name="about"),
    path("help/", views.home.Help.as_view(), name="help"),  # Add this line for the Help page
    path(
        "user/profile/", login_required(views.profile.UserProfile.as_view()), name="user_profile"
    ),
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
    path(
        "submission-group-table/",
        login_required(views.profile.submission_group_table),
        name="submission_group_table",
    ),
    path(
        "in-progress-submission-table/",
        login_required(views.profile.in_progress_submission_table),
        name="in_progress_submission_table",
    ),
    path(
        "submission-table/",
        login_required(views.profile.submission_table),
        name="submission_table",
    ),
    path(
        "create-submission-group-modal",
        login_required(views.profile.SubmissionGroupModalCreateView.as_view()),
        name="create_submission_group_modal",
    ),
    path(
        "delete-submission-group-modal/<uuid:uuid>/",
        login_required(views.profile.delete_submission_group),
        name="delete_submission_group_modal",
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
                name="activation_invalid",
            ),
            path(
                "account/activation/<uidb64>/<token>/",
                views.account.ActivateAccount.as_view(),
                name="activate_account",
            ),
        ]
    )
