import logging

import django_rq
from django_rq.management.commands import rqscheduler

from recordtransfer.jobs import cleanup_expired_sessions

scheduler = django_rq.get_scheduler()
LOGGER = logging.getLogger(__name__)


def clear_scheduled_jobs() -> None:
    """Delete any existing jobs in the scheduler when the app starts up."""
    for job in scheduler.get_jobs():
        LOGGER.debug("Deleting scheduled job %s", job)
        job.delete()


def register_scheduled_jobs() -> None:
    """Register jobs to be run on a schedule."""
    schedule = "*/2 * * * *"
    LOGGER.info(
        "Scheduling cleanup job (schedule: %s)",
        schedule,
    )
    scheduler.cron(schedule, func=cleanup_expired_sessions, queue_name="default")


class Command(rqscheduler.Command):
    def handle(self, *args, **kwargs):
        # This is necessary to prevent dupes
        clear_scheduled_jobs()
        register_scheduled_jobs()
        super(Command, self).handle(*args, **kwargs)
