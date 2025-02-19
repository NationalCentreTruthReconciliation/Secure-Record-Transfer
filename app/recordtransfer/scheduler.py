from django_rq import get_scheduler

from recordtransfer.jobs import cleanup_expired_sessions


def schedule_cleanup_jobs() -> None:
    scheduler = get_scheduler('default')

    # Schedule cleanup to run every hour
    scheduler.cron(
        "*/2 * * * *",  # Run every 2 minutes
        func=cleanup_expired_sessions,
        queue_name='default'
    )
