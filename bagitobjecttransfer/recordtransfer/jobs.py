import logging
from pathlib import Path
from datetime import timedelta

import django_rq
from django.contrib.auth.models import User
from django.utils import timezone

from recordtransfer import settings
from recordtransfer.bagger import create_bag
from recordtransfer.reporter import write_report
from recordtransfer.metadatagenerator import HtmlDocument, BagitTags
from recordtransfer.models import Bag, UploadedFile
from recordtransfer.settings import BAG_STORAGE_FOLDER, ARCHIVIST_EMAILS


LOGGER = logging.getLogger(__name__)


@django_rq.job
def bag_user_metadata_and_files(form_data: dict, user_submitted: User):
    tag_generator = BagitTags(form_data)
    tags = tag_generator.generate()

    LOGGER.info('Starting bag creation')

    folder = str(BAG_STORAGE_FOLDER)
    bagging_result = create_bag(folder, form_data['session_token'], tags, None, True)

    if bagging_result['bag_created']:
        bag_location = bagging_result['bag_location']
        bagging_time = bagging_result['time_created']
        form_data['storage_location'] = bag_location
        form_data['creation_time'] = str(bagging_time)
        doc_generator = HtmlDocument(form_data)
        html_document = doc_generator.generate()

        LOGGER.info('Starting report generation')

        report_result = write_report(REPORT_FOLDER, html_document, 'html', None)
        report_location = report_result['report_location']
        report_created = report_result['report_created']
        if report_created:
            LOGGER.info('Generated HTML document')
        else:
            LOGGER.info('HTML document generation failed')

        # Create object to be viewed in admin app
        bag_name = Path(bag_location).name
        new_bag = Bag(bagging_date=bagging_time, bag_name=bag_name, user=user_submitted)
        if report_created:
            new_bag.report_name = Path(report_location).name
            new_bag.report_contents = html_document
        new_bag.save()
        send_success_email_to_archivist()
    else:
        LOGGER.warning('Could not generate HTML document since bag creation failed')

@django_rq.job
def send_success_email_to_archivist():
    for archivist in settings.ARCHIVIST_EMAILS:
        LOGGER.info(f'Sending success email to {archivist}')

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

