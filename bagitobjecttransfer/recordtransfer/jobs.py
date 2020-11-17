import json
import logging
import smtplib
import urllib.parse
import zipfile
from io import BytesIO
from pathlib import Path
from datetime import timedelta

import django_rq
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from recordtransfer.bagger import create_bag
from recordtransfer.caais import convert_transfer_form_to_meta_tree, flatten_meta_tree
from recordtransfer.models import Bag, UploadedFile, User, Job
from recordtransfer.settings import BAG_STORAGE_FOLDER, DO_NOT_REPLY_EMAIL, BASE_URL
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import html_to_text, zip_directory


LOGGER = logging.getLogger('rq.worker')


@django_rq.job
def bag_user_metadata_and_files(form_data: dict, user_submitted: User):
    ''' This job does three things. First, it converts the form data the user submitted into BagIt
    tags. Second, it creates a bag in the user's folder under the BAG_STORAGE_FOLDER with all of
    the user's submitted files and the BagIt tag metadata. Finally, it sends an email out on
    whether the new bag was submitted without errors or with errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form.
        user_submitted (User): The user who submitted the data and files.
    '''
    LOGGER.info(msg='Creating a bag from the transfer submitted by {0}'.format(str(user_submitted)))

    # Get folder to store bag in, set the storage location in form
    folder = Path(BAG_STORAGE_FOLDER) / user_submitted.username
    if not folder.exists():
        folder.mkdir()
        LOGGER.info(msg=('Created new transfer folder for user "{0}" at {1}'.format(
            user_submitted.username, str(folder))))
    form_data['storage_location'] = str(folder.resolve())

    LOGGER.info(msg='Creating serializable CAAIS metadata from form data')
    caais_metadata = convert_transfer_form_to_meta_tree(form_data)
    LOGGER.info(msg='Flattening CAAIS metadata to be used as BagIt tags')
    bagit_tags = flatten_meta_tree(caais_metadata)

    LOGGER.info(msg='Creating bag on filesystem')
    bagging_result = create_bag(
        storage_folder=str(folder),
        session_token=form_data['session_token'],
        metadata=bagit_tags,
        bag_identifier=None,
        deletefiles=True)

    if bagging_result['bag_created']:
        LOGGER.info('bagger reported that the bag was created successfully')
        bag_location = bagging_result['bag_location']
        bagging_time = bagging_result['time_created']

        # Create object to be viewed in admin app
        bag_name = Path(bag_location).name
        new_bag = Bag(
            bagging_date=bagging_time,
            bag_name=bag_name,
            user=user_submitted,
            caais_metadata=json.dumps(caais_metadata))
        new_bag.save()

        LOGGER.info('Sending transfer success email to administrators')
        # TODO: I'm not sure this is a good approach to getting the object change URL
        bag_url = urllib.parse.urljoin(BASE_URL, f'/admin/recordtransfer/bag/{new_bag.id}')
        send_bag_creation_success.delay(form_data, bag_url, user_submitted)
        # TODO: Implement
        # TODO: LOGGER.info('Sending thank you email to user')
    else:
        LOGGER.error('bagger reported that the bag was NOT created successfully')
        LOGGER.info('Sending transfer failure email to administrators')
        send_bag_creation_failure.delay(form_data, user_submitted)
        # TODO: Implement
        # TODO: LOGGER.info('Sending transfer issue email to user')

@django_rq.job
def create_downloadable_bag(bag: Bag, user_triggered: User):
    ''' Create a zipped bag that a user can download using a Job model.

    Args:
        bag (Bag): The bag to zip up for users to download
        user (User): The user who triggered this new Job creation
    '''
    LOGGER.info(msg='Creating zipped bag from {0}'.format(str(bag.location)))

    description = (
        '{user} triggered this job to generate a download link for a transfer submitted by '
        '{bag_user}.'
    ).format(user=user_triggered.get_full_name(), bag_user=bag.user.get_full_name())

    new_job = Job(
        name=f'Generate Download Link for {str(bag)}',
        description=description,
        start_time=timezone.now(),
        user_triggered=user_triggered,
        job_status=Job.JobStatus.NOT_STARTED)
    new_job.save()

    zipf = None
    try:
        new_job.job_status = Job.JobStatus.IN_PROGRESS
        new_job.save()

        LOGGER.info(msg='Zipping directory to an in-memory file ...')
        zipf = BytesIO()
        zipped_bag = zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False)
        zip_directory(bag.location, zipped_bag)
        zipped_bag.close()
        LOGGER.info(msg='Zipped directory successfully')

        file_name = f'{bag.user.username}-{bag.bag_name}.zip'
        LOGGER.info(msg='Saving zip file as {0} ...'.format(file_name))
        new_job.attached_file.save(file_name, ContentFile(zipf.getvalue()), save=True)
        LOGGER.info(msg='Saved file succesfully')

        new_job.job_status = Job.JobStatus.COMPLETE
        new_job.end_time = timezone.now()
        new_job.save()

        LOGGER.info('Downloadable bag created successfully')
    except Exception as exc:
        new_job.job_status = Job.JobStatus.FAILED
        new_job.save()
        LOGGER.error(msg=('Creating zipped bag failed: {0}'.format(str(exc))))
    finally:
        if zipf is not None:
            zipf.close()


@django_rq.job
def send_bag_creation_success(form_data: dict, bag_url: str, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    were no errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        bag_url (str): An absolute link that links to the bag in the administrator site.
        user_submitted (User): The user who submitted the data and files.
    '''
    LOGGER.info('Finding Users to send "transfer ready" email to')
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.warning(msg=('There are no users configured to receive "transfer ready" emails.'))
        return
    recipient_list = list(recipients)
    LOGGER.info(msg=('Found {0} Users(s) to send email to: {1}'.format(
        len(recipient_list), recipient_list)))
    recipient_emails = [str(e) for e in recipients.values_list('email', flat=True)]
    try:
        LOGGER.info('Rendering HTML email from bag_submit_success.html')
        msg_html = render_to_string('recordtransfer/email/bag_submit_success.html', context={
            'user': user_submitted,
            'form_data': form_data,
            'bag_url': bag_url,
        })
        LOGGER.info('Stripping tags from rendered HTML to create a plaintext email')
        msg_plain = html_to_text(msg_html)

        LOGGER.info('Sending mail:')
        LOGGER.info('SUBJECT: New Transfer Ready for Review')
        LOGGER.info(msg='TO: {0}'.format(recipient_emails))
        LOGGER.info(msg='FROM: {0}'.format(DO_NOT_REPLY_EMAIL))
        send_mail(
            subject='New Transfer Ready for Review',
            message=msg_plain,
            from_email=DO_NOT_REPLY_EMAIL,
            recipient_list=recipient_emails,
            html_message=msg_html,
            fail_silently=False,
        )
        LOGGER.info(msg='{0} email(s) sent'.format(len(recipient_emails)))
    except smtplib.SMTPException as exc:
        LOGGER.error(msg=('Error when sending email to users: {0}'.format(str(exc))))


@django_rq.job
def send_bag_creation_failure(form_data: dict, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user who submitted the data and files.
    '''
    LOGGER.info('Finding Users to send "transfer failure" email to')
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.warning(msg=('There are no users configured to receive "transfer failure" emails'))
        return
    recipient_list = list(recipients)
    LOGGER.info(msg=('Found {0} Users(s) to send email to: {1}'.format(
        len(recipient_list), recipient_list)))
    recipient_emails = [str(e) for e in recipients.values_list('email', flat=True)]
    try:
        LOGGER.info('Rendering HTML email from bag_submit_failure.html')
        msg_html = render_to_string('recordtransfer/email/bag_submit_failure.html', context={
            'user': user_submitted,
            'form_data': form_data,
        })
        LOGGER.info('Stripping tags from rendered HTML to create a plaintext email')
        msg_plain = html_to_text(msg_html)

        LOGGER.info('Sending mail:')
        LOGGER.info('SUBJECT: Bag Creation Failed')
        LOGGER.info(msg='TO: {0}'.format(recipient_emails))
        LOGGER.info(msg='FROM: {0}'.format(DO_NOT_REPLY_EMAIL))
        send_mail(
            subject='Bag Creation Failed',
            message=msg_plain,
            from_email=DO_NOT_REPLY_EMAIL,
            recipient_list=recipient_emails,
            html_message=msg_html,
            fail_silently=False,
        )
        LOGGER.info(msg='{0} email(s) sent'.format(len(recipient_emails)))
    except smtplib.SMTPException as exc:
        LOGGER.error(msg=('Error when sending emails to users: {0}'.format(str(exc))))


@django_rq.job
def send_accession_report_to_user(form_data: dict, user_submitted: User):
    ''' Send an accession report to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user who submitted the data and files.
    '''
    recipient = [user_submitted.email]
    LOGGER.info(msg=('Sending "accession report" email to: {0}'.format(recipient[0])))
    try:
        LOGGER.info('Rendering HTML email from accession_report.html')
        msg_html = render_to_string('recordtransfer/email/accession_report.html', context={
            'user': user_submitted,
            'form_data': form_data,
        })
        LOGGER.info('Stripping tags from rendered HTML to create a plaintext email')
        msg_plain = html_to_text(msg_html)

        LOGGER.info('Sending mail:')
        LOGGER.info('SUBJECT: Thanks For Your Transfer')
        LOGGER.info(msg='TO: {0}'.format(recipient))
        LOGGER.info(msg='FROM: {0}'.format(DO_NOT_REPLY_EMAIL))
        send_mail(
            subject='Thanks For Your Transfer',
            message=msg_plain,
            from_email=DO_NOT_REPLY_EMAIL,
            recipient_list=recipient,
            html_message=msg_html,
            fail_silently=False,
        )
        LOGGER.info('1 email sent')
    except smtplib.SMTPException as exc:
        LOGGER.error(msg=('Error when sending email to user: {0}'.format(str(exc))))


@django_rq.job
def send_user_activation_email(new_user: User):
    ''' Send an activation email to the new user who is attempting to create an account. The user
    must visit the link to activate their account.

    Args:
        new_user (User): The new user who requested an account
    '''
    recipient = [new_user.email]
    LOGGER.info(msg=('Sending "account activation" email to: {0}'.format(recipient[0])))
    try:
        token = account_activation_token.make_token(new_user)
        LOGGER.info(msg='Generated token for activation link: {0}'.format(token))

        LOGGER.info('Rendering HTML email from activate_account.html')
        msg_html = render_to_string('recordtransfer/email/activate_account.html', context={
            'user': new_user,
            'base_url': BASE_URL,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'token': token,
        })
        LOGGER.info('Stripping tags from rendered HTML to create a plaintext email')
        msg_plain = html_to_text(msg_html)

        LOGGER.info('Sending mail:')
        LOGGER.info('SUBJECT: Activate Your Account')
        LOGGER.info(msg='TO: {0}'.format(recipient))
        LOGGER.info(msg='FROM: {0}'.format(DO_NOT_REPLY_EMAIL))
        send_mail(
            subject='Activate Your Account',
            message=msg_plain,
            from_email=DO_NOT_REPLY_EMAIL,
            recipient_list=recipient,
            html_message=msg_html,
            fail_silently=False
        )
        LOGGER.info('1 email sent')
    except smtplib.SMTPException as exc:
        LOGGER.error(msg=('Error when sending email to user: {0}'.format(str(exc))))


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
