from io import BytesIO
import logging
import pickle
import shutil
import zipfile
import os.path

import django_rq
from django.core.files.base import ContentFile
from django.utils import timezone

from recordtransfer.models import User, Job, Submission
from bagitobjecttransfer.settings import base
from recordtransfer.utils import zip_directory


LOGGER = logging.getLogger("rq.worker")


@django_rq.job
def create_downloadable_bag(submission: Submission, user_triggered: User):
    """Create a zipped BagIt bag that a user can download through a Job.

    Args:
        submission (Submission): The submission to create a BagIt bag for
        user_triggered (User): The user who triggered this new Job creation
    """
    LOGGER.info("Creating zipped bag from %s", submission.location)

    description = (
        f"{str(user_triggered)} triggered this job to generate a download link " "for a submission"
    )

    new_job = Job(
        name=f"Generate Downloadable Bag for {str(submission)}",
        description=description,
        start_time=timezone.now(),
        user_triggered=user_triggered,
        job_status=Job.JobStatus.IN_PROGRESS,
        submission=submission,
    )
    new_job.save()

    if not os.path.exists(submission.location):
        LOGGER.info("No bag exists at %s, creating it now.", str(submission.location))
        result = submission.make_bag(algorithms=base.BAG_CHECKSUMS, logger=LOGGER)
        if (
            len(result["missing_files"]) != 0
            or not result["bag_created"]
            or not result["bag_valid"]
            or result["time_created"] is None
        ):
            new_job.job_status = Job.JobStatus.FAILED
            new_job.save()
            return

    zipf = None
    try:
        LOGGER.info("Zipping directory to an in-memory file ...")
        zipf = BytesIO()
        zipped_bag = zipfile.ZipFile(zipf, "w", zipfile.ZIP_DEFLATED, False)
        zip_directory(submission.location, zipped_bag)
        zipped_bag.close()
        LOGGER.info("Zipped directory successfully")

        file_name = f"{user_triggered.username}-{submission.bag_name}.zip"
        LOGGER.info("Saving zip file as %s ...", file_name)
        new_job.attached_file.save(file_name, ContentFile(zipf.getvalue()), save=True)
        LOGGER.info("Saved file successfully")

        new_job.job_status = Job.JobStatus.COMPLETE
        new_job.end_time = timezone.now()
        new_job.save()

        LOGGER.info("Downloadable bag created successfully")
    except Exception as exc:
        new_job.job_status = Job.JobStatus.FAILED
        new_job.save()
        LOGGER.error(
            "Creating zipped bag failed due to exception, %s: %s", exc.__class__.__name__, str(exc)
        )
    finally:
        if zipf is not None:
            zipf.close()
        if os.path.exists(submission.location):
            LOGGER.info("Removing bag from disk after zip generation.")
            shutil.rmtree(submission.location)
