from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.cache import cache_page, never_cache

from . import views

# Pages are cached by default. If a URL should not be cached, use never_cache()

ONE_HOUR = 60 * 60

app_name = "recordtransfer"
urlpatterns = [
    path("", views.home.Index.as_view(), name="index"),
    path(
        "submission/<uuid:uuid>/csv/",
        never_cache(login_required(views.post_submission.submission_csv_export)),
        name="submission_csv",
    ),
    path(
        "submission/<uuid:uuid>/",
        never_cache(login_required(views.post_submission.SubmissionDetailView.as_view())),
        name="submission_detail",
    ),
    path(
        "submission/",
        never_cache(login_required(views.pre_submission.SubmissionFormWizard.as_view())),
        name="submit",
    ),
    path(
        "submission/open-sessions/",
        never_cache(login_required(views.pre_submission.OpenSessions.as_view())),
        name="open_sessions",
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
        never_cache(login_required(views.profile.delete_in_progress_submission)),
        name="delete_in_progress_submission_modal",
    ),
    path("about/", views.home.About.as_view(), name="about"),
    # Cache for one hour only - admins may change terms shown on this page
    path("help/", cache_page(ONE_HOUR)(views.home.Help.as_view()), name="help"),
    path(
        "user/profile/",
        never_cache(login_required(views.profile.UserProfile.as_view())),
        name="user_profile",
    ),
    path(
        "user/profile/account-info/",
        never_cache(login_required(views.profile.AccountInfoUpdateView.as_view())),
        name="account_info_update",
    ),
    path(
        "user/profile/contact-info/",
        never_cache(login_required(views.profile.ContactInfoUpdateView.as_view())),
        name="contact_info_update",
    ),
    path(
        "submission-group/<uuid:uuid>/",
        never_cache(login_required(views.post_submission.SubmissionGroupDetailView.as_view())),
        name="submission_group_detail",
    ),
    path(
        "submission-group/<uuid:uuid>/csv/",
        never_cache(login_required(views.post_submission.submission_group_bulk_csv_export)),
        name="submission_group_bulk_csv",
    ),
    path(
        "user/submission-group/",
        never_cache(login_required(views.post_submission.get_user_submission_groups)),
        name="get_user_submission_groups",
    ),
    path(
        "job/<uuid:job_uuid>/file/",
        login_required(views.media.job_file),
        name="job_file",
    ),
    path(
        "submission-group-table/",
        never_cache(login_required(views.profile.submission_group_table)),
        name="submission_group_table",
    ),
    path(
        "in-progress-submission-table/",
        never_cache(login_required(views.profile.in_progress_submission_table)),
        name="in_progress_submission_table",
    ),
    path(
        "submission-table/",
        never_cache(login_required(views.profile.submission_table)),
        name="submission_table",
    ),
    path(
        "open-session-table/",
        never_cache(login_required(views.pre_submission.open_session_table)),
        name="open_session_table",
    ),
    path(
        "create-submission-group-modal",
        never_cache(login_required(views.profile.SubmissionGroupModalCreateView.as_view())),
        name="create_submission_group_modal",
    ),
    path(
        "delete-submission-group-modal/<uuid:uuid>/",
        never_cache(login_required(views.profile.delete_submission_group)),
        name="delete_submission_group_modal",
    ),
    path(
        "assign-submission-group-modal/<uuid:uuid>/",
        never_cache(login_required(views.profile.assign_submission_group_modal)),
        name="assign_submission_group_modal",
    ),
    path(
        "assign-submission-group",
        never_cache(login_required(views.profile.assign_submission_group)),
        name="assign_submission_group",
    ),
]

if settings.TESTING or settings.SIGN_UP_ENABLED:
    urlpatterns.extend(
        [
            path(
                "account/",
                never_cache(views.account.CreateAccount.as_view()),
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
                never_cache(views.account.ActivateAccount.as_view()),
                name="activate_account",
            ),
        ]
    )
