from datetime import timedelta

from django.conf import settings
from django_rq import get_scheduler

from recordtransfer.emails import send_user_in_progress_submission_expiring
from recordtransfer.models import InProgressSubmission

scheduler = get_scheduler()


def schedule_in_progress_submission_expiring_email(in_progress: InProgressSubmission) -> None:
    """Schedule an email job to remind a user of an expiring in-progress submission.

    Args:
        in_progress: The in-progress submission to remind the user about
    """
    if (
        settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES == -1
        or settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES == -1
    ):
        return
    scheduler.enqueue_in(
        timedelta(
            minutes=(
                settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
                - settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
            )
        ),
        send_user_in_progress_submission_expiring,
        in_progress,
    )
