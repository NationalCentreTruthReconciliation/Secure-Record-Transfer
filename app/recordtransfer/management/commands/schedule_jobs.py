import logging

import django_rq
from django.conf import settings
from django_rq.management.commands import rqscheduler

from recordtransfer.jobs import check_expiring_in_progress_submissions, cleanup_expired_sessions

scheduler = django_rq.get_scheduler()
LOGGER = logging.getLogger(__name__)


def clear_scheduled_jobs() -> None:
    """Delete any existing jobs in the scheduler when the app starts up."""
    for job in scheduler.get_jobs():
        LOGGER.debug("Deleting scheduled job %s", job)
        job.delete()


def register_scheduled_jobs() -> None:
    """Register jobs to be run on a schedule."""
    if (
        settings.FILE_UPLOAD_ENABLED
        and settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES != -1
    ):
        cleanup_schedule = settings.UPLOAD_SESSION_EXPIRED_CLEANUP_SCHEDULE
        LOGGER.info(
            "Scheduling cleanup job (schedule: %s)",
            cleanup_schedule,
        )
        scheduler.cron(cleanup_schedule, func=cleanup_expired_sessions, queue_name="default")

        email_schedule = settings.IN_PROGRESS_SUBMISSION_EXPIRING_EMAIL_SCHEDULE
        LOGGER.info(
            "Scheduling expiring email job (schedule: %s)",
            email_schedule,
        )
        scheduler.cron(
            email_schedule, func=check_expiring_in_progress_submissions, queue_name="default"
        )


class Command(rqscheduler.Command):
    def handle(self, *args, **kwargs):
        # This is necessary to prevent dupes
        clear_scheduled_jobs()
        register_scheduled_jobs()
        super(Command, self).handle(*args, **kwargs)
