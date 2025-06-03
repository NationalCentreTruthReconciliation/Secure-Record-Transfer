import logging
import os.path
import shutil
import tempfile
import zipfile

import django_rq
from django.conf import settings
from django.core.files.base import File
from django.db.models.query import QuerySet
from django.utils import timezone

from recordtransfer.emails import send_user_in_progress_submission_expiring
from recordtransfer.handlers import JobLogHandler
from recordtransfer.models import InProgressSubmission, Job, Submission, UploadSession, User
from recordtransfer.utils import zip_directory

LOGGER = logging.getLogger(__name__)


@django_rq.job
def create_downloadable_bag(submission: Submission, user_triggered: User) -> None:
    """Create a zipped BagIt bag that a user can download through a Job.

    Args:
        submission (Submission): The submission to create a BagIt bag for
        user_triggered (User): The user who triggered this new Job creation
    """
    description = (
        f"{user_triggered!s} triggered this job to generate a download link for a submission"
    )

    new_job = Job(
        name=f"Generate Downloadable Bag for {submission!s}",
        description=description,
        start_time=timezone.now(),
        user_triggered=user_triggered,
        job_status=Job.JobStatus.IN_PROGRESS,
    )
    new_job.save()

    # Set up job logging handler
    job_handler = JobLogHandler(new_job)
    job_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    LOGGER.addHandler(job_handler)

    try:
        LOGGER.info("Creating zipped bag from %s", submission.location)

        if not os.path.exists(submission.location):
            LOGGER.info("No bag exists at %s, creating it now.", str(submission.location))
            submission.make_bag(algorithms=settings.BAG_CHECKSUMS)

        if not os.path.exists(settings.TEMP_STORAGE_FOLDER):
            os.makedirs(settings.TEMP_STORAGE_FOLDER, exist_ok=True)

        with tempfile.TemporaryFile(
            suffix=".zip", dir=settings.TEMP_STORAGE_FOLDER
        ) as temp_zip_file:
            LOGGER.info(
                "Creating temporary zip file on disk at %s ...",
                f"{settings.TEMP_STORAGE_FOLDER}/{temp_zip_file.name}.zip",
            )
            zip_directory(
                submission.location,
                zipfile.ZipFile(temp_zip_file, "w", zipfile.ZIP_DEFLATED, False),
            )
            LOGGER.info("Zipped directory successfully")

            file_name = f"{user_triggered.username}-{submission.bag_name}.zip"
            LOGGER.info("Saving zip file as %s ...", file_name)
            new_job.attached_file.save(file_name, File(temp_zip_file), save=True)
            LOGGER.info("Saved file successfully")

            new_job.job_status = Job.JobStatus.COMPLETE
            new_job.end_time = timezone.now()
            new_job.save()

            LOGGER.info("Downloadable bag created successfully")

    except Exception as exc:
        new_job.job_status = Job.JobStatus.FAILED
        new_job.save()
        LOGGER.error("Creating zipped bag failed due to exception!", exc_info=exc)

    finally:
        if os.path.exists(submission.location):
            LOGGER.info("Removing bag from disk after zip generation.")
            shutil.rmtree(submission.location)

        LOGGER.removeHandler(job_handler)
        job_handler.close()


@django_rq.job
def cleanup_expired_sessions() -> None:
    """Clean up UploadSession objects that are expirable. Upload sessions that are not associated
    with any InProgressSubmission objects are deleted, while those that are associated with
    InProgressSubmission objects have their uploads removed and are expired.
    """
    LOGGER.info("Cleaning up upload sessions ...")
    try:
        expirable_sessions: QuerySet[UploadSession] = UploadSession.objects.get_expirable().all()
        deletable_sessions: QuerySet[UploadSession] = UploadSession.objects.get_deletable().all()
        expirable_count = expirable_sessions.count()
        deletable_count = deletable_sessions.count()
        if expirable_count == 0 and deletable_count == 0:
            LOGGER.info("No expired upload sessions to clean up")
            return

        for session in expirable_sessions:
            session.expire()
        for session in deletable_sessions:
            session.delete()

        LOGGER.info(
            "Cleaned up %d upload sessions; expired %d and deleted %d",
            expirable_count + deletable_count,
            expirable_count,
            deletable_count,
        )

    except Exception as e:
        LOGGER.exception("Error cleaning up expired upload sessions: %s", str(e))
        raise e


@django_rq.job
def check_expiring_in_progress_submissions() -> None:
    """Check for in-progress submissions that are about to expire for which reminder emails have
    not been sent yet, and send email reminders.
    """
    LOGGER.info(
        "Checking for in-progress submissions that are about to expire without reminder emails "
        "sent yet ..."
    )
    try:
        expiring = InProgressSubmission.objects.get_expiring_without_reminder().all()

        count = expiring.count()
        if count == 0:
            LOGGER.info("No in-progress submissions are about to expire")
            return

        for in_progress in expiring:
            send_user_in_progress_submission_expiring.delay(in_progress)
            in_progress.reminder_email_sent = True
            in_progress.save()

        LOGGER.info(
            "Sent reminders for %d in-progress submissions that are about to expire",
            count,
        )

    except Exception as e:
        LOGGER.exception(
            "Error checking for in-progress submissions that are about to expire: %s", str(e)
        )
        raise e
