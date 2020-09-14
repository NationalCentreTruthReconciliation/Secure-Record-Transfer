import logging
import smtplib
from pathlib import Path
from datetime import timedelta

import django_rq
from django.core.mail import send_mail
from django.utils import timezone

from recordtransfer.bagger import create_bag
from recordtransfer.metadatagenerator import HtmlDocument, BagitTags
from recordtransfer.filecounter import get_human_readable_file_count
from recordtransfer.models import Bag, UploadedFile
from recordtransfer.settings import BAG_STORAGE_FOLDER, ARCHIVIST_EMAILS


LOGGER = logging.getLogger(__name__)


@django_rq.job
def bag_user_metadata_and_files(form_data: dict, user_submitted):
    file_names = list(map(str, UploadedFile.objects.filter(
        session__token=form_data['session_token']
    ).filter(
        old_copy_removed=False
    ).values_list('name', flat=True)))

    form_data['file_count_message'] = get_human_readable_file_count(file_names)

    tag_generator = BagitTags(form_data)
    tags = tag_generator.generate()

    LOGGER.info('Starting bag creation')

    folder = Path(BAG_STORAGE_FOLDER) / user_submitted.username
    if not folder.exists():
        folder.mkdir()

    bagging_result = create_bag(
        storage_folder=str(folder),
        session_token=form_data['session_token'],
        metadata=tags,
        bag_identifier=None,
        deletefiles=True)

    if bagging_result['bag_created']:
        bag_location = bagging_result['bag_location']
        bagging_time = bagging_result['time_created']
        form_data['storage_location'] = bag_location
        form_data['creation_time'] = str(bagging_time)

        LOGGER.info('Starting report generation')
        doc_generator = HtmlDocument(form_data)
        html_document = doc_generator.generate()

        # Create object to be viewed in admin app
        bag_name = Path(bag_location).name
        new_bag = Bag(bagging_date=bagging_time, bag_name=bag_name, user=user_submitted)
        new_bag.report_contents = html_document
        new_bag.save()
        send_bag_creation_success.delay(form_data, user_submitted)
    else:
        LOGGER.warning('Could not generate HTML document since bag creation failed')
        send_bag_creation_failure.delay(form_data, user_submitted)

@django_rq.job
def send_bag_creation_success(form_data: dict, user_submitted):
    LOGGER.info(msg=('Sending "bag ready" email to %s' % ARCHIVIST_EMAILS))
    message = (f'User {user_submitted.username} submitted files that are ready for review.'
               f'\nThe title of the records is {form_data["collection_title"]}.')
    try:
        send_mail(
            subject='New Bag Ready For Review',
            message=message,
            from_email='donotreply@127.0.0.1:8000',
            recipient_list=ARCHIVIST_EMAILS,
            fail_silently=False,
        )
    except smtplib.SMTPException as exc:
        LOGGER.warning(msg=('Error when sending emails to archivist(s): %s' % str(exc)))


@django_rq.job
def send_bag_creation_failure(form_data: dict, user_submitted):
    LOGGER.info(msg=('Sending "bag failure" email to %s' % ARCHIVIST_EMAILS))
    message = (f'Bag creation failed for the file submitted by user {user_submitted.username}')
    try:
        send_mail(
            subject='Bag Creation Failed',
            message=message,
            from_email='donotreply@127.0.0.1:8000',
            recipient_list=ARCHIVIST_EMAILS,
            fail_silently=False,
        )
    except smtplib.SMTPException as exc:
        LOGGER.warning(msg=('Error when sending emails to archivist(s): %s' % str(exc)))

@django_rq.job
def clean_undeleted_temp_files(hours=12):
    ''' Deletes every temp file tracked in the database older than a specified number of hours.

    Args:
        hours (int): The threshold number of hours in the past required to delete a file
    '''
    time_threshold = timezone.now() - timedelta(hours=hours)

    old_undeleted_files = UploadedFile.objects.filter(
        old_copy_removed=False
    ).filter(
        session__started_at__lt=time_threshold
    )

    LOGGER.info('Running cleaning')

    for upload in old_undeleted_files:
        upload.delete_file()
