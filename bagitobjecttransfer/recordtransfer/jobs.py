import json
import logging
import smtplib
import urllib.parse
from pathlib import Path
from datetime import timedelta

import django_rq
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.html import strip_tags
from django.template.loader import render_to_string

from recordtransfer.bagger import create_bag
from recordtransfer.caais import convert_transfer_form_to_meta_tree, convert_meta_tree_to_bagit_tags
from recordtransfer.models import Bag, UploadedFile, User
from recordtransfer.settings import BAG_STORAGE_FOLDER, DO_NOT_REPLY_EMAIL, BASE_URL


LOGGER = logging.getLogger(__name__)


@django_rq.job
def bag_user_metadata_and_files(form_data: dict, user_submitted: User):
    ''' This job does three things. First, it converts the form data the user submitted into BagIt \
    tags. Second, it creates a bag in the user's folder under the BAG_STORAGE_FOLDER with all of \
    the user's submitted files and the BagIt tag metadata. Finally, it sends an email out on \
    whether the new bag was submitted without errors or with errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form.
        user_submitted (User): The user who submitted the data and files.
    '''
    LOGGER.info('Starting bag creation')

    caais_metadata = convert_transfer_form_to_meta_tree(form_data)
    bagit_tags = convert_meta_tree_to_bagit_tags(caais_metadata)

    folder = Path(BAG_STORAGE_FOLDER) / user_submitted.username
    if not folder.exists():
        folder.mkdir()

    bagging_result = create_bag(
        storage_folder=str(folder),
        session_token=form_data['session_token'],
        metadata=bagit_tags,
        bag_identifier=None,
        deletefiles=True)

    if bagging_result['bag_created']:
        bag_location = bagging_result['bag_location']
        bagging_time = bagging_result['time_created']
        form_data['storage_location'] = bag_location
        form_data['creation_time'] = str(bagging_time)

        # Create object to be viewed in admin app
        bag_name = Path(bag_location).name
        new_bag = Bag(bagging_date=bagging_time, bag_name=bag_name, user=user_submitted)
        new_bag.caais_metadata = json.dumps(caais_metadata)
        new_bag.save()
        # TODO: I'm not sure this is a good approach to getting the object change URL
        bag_url = urllib.parse.urljoin(BASE_URL, f'/admin/recordtransfer/bag/{new_bag.id}')
        send_bag_creation_success.delay(form_data, bag_url, user_submitted)
    else:
        LOGGER.warning('Could not generate HTML document since bag creation failed')
        send_bag_creation_failure.delay(form_data, user_submitted)


@django_rq.job
def send_bag_creation_success(form_data: dict, bag_url: str, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    were no errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
        the CAAIS version of the form.
        bag_url (str): An absolute link that links to the bag in the administrator site.
        user_submitted (User): The user who submitted the data and files.
    '''
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.info(msg=('There are no users configured to receive bag info update emails.'))
        return

    LOGGER.info(msg=('Sending "bag ready" email to: %s' % list(recipients)))
    recipient_emails = list(map(str, recipients.values_list('email', flat=True) ))
    try:
        msg_html = render_to_string('recordtransfer/email/bag_submit_success.html', context={
            'user': user_submitted,
            'form_data': form_data,
            'bag_url': bag_url,
        })
        msg_plain = strip_tags(msg_html)

        send_mail(
            subject='New Bag Ready for Review',
            message=msg_plain,
            from_email=DO_NOT_REPLY_EMAIL,
            recipient_list=recipient_emails,
            html_message=msg_html,
            fail_silently=False,
        )
    except smtplib.SMTPException as exc:
        LOGGER.warning(msg=('Error when sending emails to users: %s' % str(exc)))


@django_rq.job
def send_bag_creation_failure(form_data: dict, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
        the CAAIS version of the form.
        user_submitted (User): The user who submitted the data and files.
    '''
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.info(msg=('There are no users configured to receive bag failure update emails.'))
        return

    LOGGER.info(msg=('Sending "bag failure" email to: %s' % list(recipients)))
    recipient_emails = list(map(str, recipients.values_list('email', flat=True) ))
    try:
        msg_html = render_to_string('recordtransfer/email/bag_submit_success.html', context={
            'user': user_submitted,
            'form_data': form_data,
        })
        msg_plain = strip_tags(msg_html)

        send_mail(
            subject='Bag Creation Failed',
            message=msg_plain,
            from_email=DO_NOT_REPLY_EMAIL,
            recipient_list=recipient_emails,
            html_message=msg_html,
            fail_silently=False,
        )
    except smtplib.SMTPException as exc:
        LOGGER.warning(msg=('Error when sending emails to users: %s' % str(exc)))


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
