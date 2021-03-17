import json
import logging
import smtplib
import zipfile
from io import BytesIO
from pathlib import Path
from datetime import timedelta

import django_rq
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from recordtransfer.bagger import create_bag
from recordtransfer.caais import convert_transfer_form_to_meta_tree, flatten_meta_tree
from recordtransfer.models import Bag, BagGroup, UploadedFile, User, Job
from recordtransfer.settings import BAG_STORAGE_FOLDER, DO_NOT_REPLY_USERNAME, ARCHIVIST_EMAIL
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
        LOGGER.info('Storing Bag in database')
        bag_name = Path(bag_location).name
        new_bag = Bag(
            bagging_date=bagging_time,
            bag_name=bag_name,
            user=user_submitted,
            caais_metadata=json.dumps(caais_metadata))
        new_bag.save()

        group_name = form_data['group_name']
        if group_name != 'No Group':
            group = None
            if group_name == 'Add New Group':
                new_group_name = form_data['new_group_name']
                description = form_data['group_description']
                group, created = BagGroup.objects.get_or_create(name=new_group_name,
                                                                description=description,
                                                                created_by=user_submitted)
                if created:
                    LOGGER.info(msg='Created "{0}" BagGroup'.format(new_group_name))
            else:
                group = BagGroup.objects.get(name=group_name, created_by=user_submitted)

            if group:
                LOGGER.info(msg='Associating Bag with "{0}" BagGroup'.format(group.name))
                new_bag.part_of_group = group
                new_bag.save()
            else:
                LOGGER.warning(msg='Could not find "{0}" BagGroup'.format(group.name))

        LOGGER.info('Sending transfer success email to administrators')
        send_bag_creation_success.delay(form_data, new_bag, user_submitted)
        LOGGER.info('Sending thank you email to user')
        send_thank_you_for_your_transfer.delay(form_data, user_submitted)
    else:
        LOGGER.error('bagger reported that the bag was NOT created successfully')
        LOGGER.info('Sending transfer failure email to administrators')
        send_bag_creation_failure.delay(form_data, user_submitted)
        LOGGER.info('Sending transfer issue email to user')
        send_your_transfer_did_not_go_through.delay(form_data, user_submitted)

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
def send_bag_creation_success(form_data: dict, bag: Bag, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    were no errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        bag (Bag): The new bag that was created.
        user_submitted (User): The user who submitted the data and files.
    '''
    subject = 'New Transfer Ready for Review'
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)
    bag_url = 'http://{domain}/{change_url}'.format(
        domain=domain.rstrip(' /'),
        change_url=bag.get_admin_change_url().lstrip(' /')
    )
    LOGGER.info(msg='Generated bag change URL: {0}'.format(bag_url))

    LOGGER.info(msg='Finding Users to send "{0}" email to'.format(subject))
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.warning(msg=('There are no users configured to receive transfer update emails.'))
        return
    user_list = list(recipients)
    LOGGER.info(msg=('Found {0} Users(s) to send email to: {1}'.format(len(user_list), user_list)))
    recipient_emails = [str(e) for e in recipients.values_list('email', flat=True)]

    send_mail_with_logs(
        recipients=recipient_emails,
        from_email=from_email,
        subject=subject,
        template_name='recordtransfer/email/bag_submit_success.html',
        context={
            'user': user_submitted,
            'form_data': form_data,
            'bag_url': bag_url,
        }
    )

@django_rq.job
def send_bag_creation_failure(form_data: dict, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user who submitted the data and files.
    '''
    subject = 'Bag Creation Failed'
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    LOGGER.info(msg='Finding Users to send "{0}" email to'.format(subject))
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.warning(msg=('There are no users configured to receive transfer update emails.'))
        return
    user_list = list(recipients)
    LOGGER.info(msg=('Found {0} Users(s) to send email to: {1}'.format(len(user_list), user_list)))
    recipient_emails = [str(e) for e in recipients.values_list('email', flat=True)]

    send_mail_with_logs(
        recipients=recipient_emails,
        from_email=from_email,
        subject=subject,
        template_name='recordtransfer/email/bag_submit_failure.html',
        context={
            'user': user_submitted,
            'form_data': form_data,
        }
    )

@django_rq.job
def send_thank_you_for_your_transfer(form_data: dict, user_submitted: User):
    ''' Send a transfer success email to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user who submitted the data and files.
    '''
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    send_mail_with_logs(
        recipients=[user_submitted.email],
        from_email=from_email,
        subject='Thank You For Your Transfer',
        template_name='recordtransfer/email/transfer_success.html',
        context={
            'user': user_submitted,
            'form_data': form_data,
            'archivist_email': ARCHIVIST_EMAIL,
        }
    )

@django_rq.job
def send_your_transfer_did_not_go_through(form_data: dict, user_submitted: User):
    ''' Send a transfer failure email to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user who submitted the data and files.
    '''
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    send_mail_with_logs(
        recipients=[user_submitted.email],
        from_email=from_email,
        subject='Issue With Your Transfer',
        template_name='recordtransfer/email/transfer_failure.html',
        context={
            'user': user_submitted,
            'form_data': form_data,
            'archivist_email': ARCHIVIST_EMAIL,
        }
    )

@django_rq.job
def send_user_activation_email(new_user: User):
    ''' Send an activation email to the new user who is attempting to create an account. The user
    must visit the link to activate their account.

    Args:
        new_user (User): The new user who requested an account
    '''
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, domain)

    token = account_activation_token.make_token(new_user)
    LOGGER.info(msg='Generated token for activation link: {0}'.format(token))

    send_mail_with_logs(
        recipients=[new_user.email],
        from_email=from_email,
        subject='Activate Your Account',
        template_name='recordtransfer/email/activate_account.html',
        context = {
            'user': new_user,
            'base_url': domain,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'token': token,
        }
    )

def send_mail_with_logs(recipients: list, from_email: str, subject, template_name: str,
                        context: dict):
    try:
        if Site.objects.get_current().domain == '127.0.0.1:8000':
            new_email = '{0}@{1}'.format(DO_NOT_REPLY_USERNAME, 'example.com')
            msg = 'Changing FROM email for local development. Using {0} instead of {1}'
            LOGGER.info(msg=msg.format(new_email, from_email))
            from_email = new_email

        LOGGER.info('Setting up new email:')
        LOGGER.info(msg='SUBJECT: {0}'.format(subject))
        LOGGER.info(msg='TO: {0}'.format(recipients))
        LOGGER.info(msg='FROM: {0}'.format(from_email))
        LOGGER.info(msg='Rendering HTML email from {0}'.format(template_name))
        msg_html = render_to_string(template_name, context=context)
        LOGGER.info('Stripping tags from rendered HTML to create a plaintext email')
        msg_plain = html_to_text(msg_html)
        LOGGER.info('Sending...')
        send_mail(
            subject=subject,
            message=msg_plain,
            from_email=from_email,
            recipient_list=recipients,
            html_message=msg_html,
            fail_silently=False
        )
        num_recipients = len(recipients)
        if num_recipients == 1:
            LOGGER.info('1 email sent')
        else:
            LOGGER.info(msg='{0} emails sent'.format(num_recipients))
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
