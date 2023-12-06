import logging
import shutil
import zipfile
from io import BytesIO
import os.path

import django_rq
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from caais.models import Metadata

from recordtransfer.caais import map_form_to_metadata
from recordtransfer.emails import (
    send_submission_creation_success,
    send_thank_you_for_your_transfer,
)
from recordtransfer.models import SubmissionGroup, UploadSession, User, Job, Submission
from recordtransfer import settings
from recordtransfer.utils import zip_directory


LOGGER = logging.getLogger('rq.worker')

@django_rq.job
def create_and_save_submission(form_data: dict, user_submitted: User):
    ''' Create database models for the submitted form. Sends an email to the
    submitting user and the staff members who receive submission email updates.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form.
        user_submitted (User): The user who submitted the data and files.
    '''
    LOGGER.info('Creating a submission from the transfer submitted by %s', str(user_submitted))

    if settings.FILE_UPLOAD_ENABLED:
        token = form_data['session_token']
        LOGGER.info('Fetching session with the token %s', token)
        upload_session = UploadSession.objects.filter(token=token).first()
    else:
        LOGGER.info((
            'No file upload session will be linked to submission due to '
            'FILE_UPLOAD_ENABLED=false'
        ))
        upload_session = None

    LOGGER.info('Mapping form data to CAAIS metadata')
    metadata: Metadata = map_form_to_metadata(form_data)

    title = metadata.accession_title
    abbrev_title = title if len(title) <= 20 else title[0:20]
    bag_name = '{username}_{datetime}_{title}'.format(
        username=slugify(user_submitted),
        datetime=timezone.localtime(timezone.now()).strftime(r'%Y%m%d-%H%M%S'),
        title=slugify(abbrev_title))

    LOGGER.info('Created name for bag: "%s"', bag_name)

    LOGGER.info('Creating Submission object linked to new metadata')
    new_submission = Submission(
        submission_date=timezone.now(),
        user=user_submitted,
        metadata=metadata,
        upload_session=upload_session,
        bag_name=bag_name,
    )
    new_submission.save()

    group_name = form_data['group_name']
    if group_name != 'No Group':
        if group_name == 'Add New Group':
            new_group_name = form_data['new_group_name']
            description = form_data['group_description']
            group, created = SubmissionGroup.objects.get_or_create(name=new_group_name,
                                                                   description=description,
                                                                   created_by=user_submitted)
            if created:
                LOGGER.info('Created "%s" SubmissionGroup', new_group_name)
        else:
            group = SubmissionGroup.objects.get(name=group_name, created_by=user_submitted)

        if group:
            LOGGER.info('Associating Submission with "%s" SubmissionGroup', group.name)
            new_submission.part_of_group = group
            new_submission.save()
        else:
            LOGGER.warning('Could not find "%s" SubmissionGroup', group.name)

    LOGGER.info('Sending transfer success email to administrators')
    send_submission_creation_success.delay(form_data, new_submission)
    LOGGER.info('Sending thank you email to user')
    send_thank_you_for_your_transfer.delay(form_data, new_submission)


@django_rq.job
def create_downloadable_bag(submission: Submission, user_triggered: User):
    ''' Create a zipped BagIt bag that a user can download through a Job.

    Args:
        submission (Submission): The submission to create a BagIt bag for
        user_triggered (User): The user who triggered this new Job creation
    '''
    LOGGER.info('Creating zipped bag from %s', submission.location)

    description = (
        f'{str(user_triggered)} triggered this job to generate a download link '
        'for a submission'
    )

    new_job = Job(
        name=f'Generate Downloadable Bag for {str(submission)}',
        description=description,
        start_time=timezone.now(),
        user_triggered=user_triggered,
        job_status=Job.JobStatus.IN_PROGRESS,
        submission=submission
    )
    new_job.save()

    if not os.path.exists(submission.location):
        LOGGER.info('No bag exists at %s, creating it now.', str(submission.location))
        result = submission.make_bag(algorithms=settings.BAG_CHECKSUMS, logger=LOGGER)
        if len(result['missing_files']) != 0 or not result['bag_created'] or not result['bag_valid'] or \
                result['time_created'] is None:
            new_job.job_status = Job.JobStatus.FAILED
            new_job.save()
            return

    zipf = None
    try:
        LOGGER.info('Zipping directory to an in-memory file ...')
        zipf = BytesIO()
        zipped_bag = zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False)
        zip_directory(submission.location, zipped_bag)
        zipped_bag.close()
        LOGGER.info('Zipped directory successfully')

        file_name = f'{user_triggered.username}-{submission.bag_name}.zip'
        LOGGER.info('Saving zip file as %s ...', file_name)
        new_job.attached_file.save(file_name, ContentFile(zipf.getvalue()), save=True)
        LOGGER.info('Saved file successfully')

        new_job.job_status = Job.JobStatus.COMPLETE
        new_job.end_time = timezone.now()
        new_job.save()

        LOGGER.info('Downloadable bag created successfully')
    except Exception as exc:
        new_job.job_status = Job.JobStatus.FAILED
        new_job.save()
        LOGGER.error(
            'Creating zipped bag failed due to exception, %s: %s',
            exc.__class__.__name__, str(exc)
        )
    finally:
        if zipf is not None:
            zipf.close()
        if os.path.exists(submission.location):
            LOGGER.info("Removing bag from disk after zip generation.")
            shutil.rmtree(submission.location)
