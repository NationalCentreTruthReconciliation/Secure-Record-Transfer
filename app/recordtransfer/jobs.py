import logging
import tempfile
import zipfile
from pathlib import Path

import django_rq
from django.conf import settings
from django.core.files.base import File
from django.db.models.query import QuerySet
from django.utils import timezone
from upload.models import UploadSession

from recordtransfer import utils
from recordtransfer.emails import send_user_in_progress_submission_expiring
from recordtransfer.handlers import JobLogHandler
from recordtransfer.models import LOGGER as RECORDTRANSFER_MODELS_LOGGER
from recordtransfer.models import InProgressSubmission, Job, Submission, User

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

    try:
        LOGGER.addHandler(job_handler)
        RECORDTRANSFER_MODELS_LOGGER.addHandler(job_handler)

        with (
            tempfile.TemporaryFile(
                suffix=".zip", dir=settings.TEMP_STORAGE_FOLDER
            ) as temp_zip_file,
            tempfile.TemporaryDirectory(
                prefix=f"Job-{new_job.pk:06d}-", dir=settings.TEMP_STORAGE_FOLDER
            ) as temp_dir,
        ):
            LOGGER.info("Creating Bag for submission %s at %s ...", repr(submission), temp_dir)

            submission.make_bag(Path(temp_dir), algorithms=settings.BAG_CHECKSUMS)

            LOGGER.info(
                "Zipping Bag to temp file on disk at %s ...",
                f"{settings.TEMP_STORAGE_FOLDER}/{temp_zip_file.name}.zip",
            )
            utils.zip_directory(
                temp_dir,
                zipfile.ZipFile(temp_zip_file, "w", zipfile.ZIP_DEFLATED, False),
            )
            LOGGER.info("Zipped directory successfully")

            file_name = f"{submission.bag_name}.zip"
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
        LOGGER.removeHandler(job_handler)
        RECORDTRANSFER_MODELS_LOGGER.removeHandler(job_handler)
        job_handler.close()


def get_expirable_upload_sessions() -> QuerySet[UploadSession]:
    """Get upload sessions that can be expired, that have an in-progress submission attached."""
    return UploadSession.objects.get_expirable().filter(in_progress_submission__isnull=False).all()


    """Get upload sessions that can be deleted, and do not have an in-progress submission."""
def get_deletable_upload_sessions() -> QuerySet[UploadSession]:
    return UploadSession.objects.get_deletable().filter(in_progress_submission__isnull=True).all()


@django_rq.job
def cleanup_expired_sessions() -> None:
    """Clean up UploadSession objects that are expirable. Upload sessions that are not associated
    with any InProgressSubmission objects are deleted, while those that are associated with
    InProgressSubmission objects have their uploads removed and are expired.
    """
    LOGGER.info("Cleaning up upload sessions ...")
    try:
        expirable_sessions = get_expirable_upload_sessions()
        deletable_sessions = get_deletable_upload_sessions()

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
