import logging
import shutil
import smtplib
import zipfile
from io import BytesIO
from datetime import timedelta
import os.path

import django_rq
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify
from django.template.loader import render_to_string

from recordtransfer.caais import convert_form_data_to_metadata
from recordtransfer.models import BagGroup, UploadedFile, UploadSession, User, Job, Submission
from recordtransfer import settings
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import html_to_text, zip_directory


LOGGER = logging.getLogger('rq.worker')


def _get_admin_recipient_list(subject):
    LOGGER.info('Finding Users to send "%s" email to', subject)
    recipients = User.objects.filter(gets_bag_email_updates=True)
    if not recipients:
        LOGGER.warning('There are no users configured to receive transfer update emails.')
        return
    user_list = list(recipients)
    LOGGER.info(
        'Found %d Users(s) to send email to: %s',
        len(user_list), str(user_list)
    )
    return [str(e) for e in recipients.values_list('email', flat=True)]


@django_rq.job
def bag_user_metadata_and_files(form_data: dict, user_submitted: User):
    ''' Create database models for the submitted form. Sends an email
    to the submitting user and the staff members who receive submission email updates.

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

    LOGGER.info('Creating serializable CAAIS metadata from form data')
    metadata = convert_form_data_to_metadata(form_data)

    title = form_data['accession_title']
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
        bag=metadata,
        upload_session=upload_session,
        bag_name=bag_name,
    )
    new_submission.save()

    group_name = form_data['group_name']
    if group_name != 'No Group':
        if group_name == 'Add New Group':
            new_group_name = form_data['new_group_name']
            description = form_data['group_description']
            group, created = BagGroup.objects.get_or_create(name=new_group_name,
                                                            description=description,
                                                            created_by=user_submitted)
            if created:
                LOGGER.info('Created "%s" BagGroup', new_group_name)
        else:
            group = BagGroup.objects.get(name=group_name, created_by=user_submitted)

        if group:
            LOGGER.info('Associating Submission with "%s" BagGroup', group.name)
            new_submission.part_of_group = group
            new_submission.save()
        else:
            LOGGER.warning('Could not find "%s" BagGroup', group.name)

    LOGGER.info('Sending transfer success email to administrators')
    send_bag_creation_success.delay(form_data, new_submission)
    LOGGER.info('Sending thank you email to user')
    send_thank_you_for_your_transfer.delay(form_data, new_submission)


@django_rq.job
def create_downloadable_bag(bag: Submission, user_triggered: User):
    ''' Create a zipped bag that a user can download using a Job model.

    Args:
        bag (Submission): The submission to zip up for users to download
        user_triggered (User): The user who triggered this new Job creation
    '''
    LOGGER.info('Creating zipped bag from %s', str(bag.location))

    description = (
        '{user} triggered this job to generate a download link for the bag '
        '{name}'
    ).format(user=str(user_triggered), name=bag.bag_name)

    if not os.path.exists(bag.location):
        LOGGER.info('No bag exists at %s, creating it now.', str(bag.location))
        result = bag.make_bag(algorithms=settings.BAG_CHECKSUMS)
        if len(result['missing_files']) != 0 or not result['bag_created'] or not result['bag_valid'] or \
                result['time_created'] is None:
            # Because we didn't generate the bag directory, exit.
            return

    new_job = Job(
        name=f'Generate Download Link for {str(bag)}',
        description=description,
        start_time=timezone.now(),
        user_triggered=user_triggered,
        job_status=Job.JobStatus.NOT_STARTED,
        submission=bag
    )
    new_job.save()

    zipf = None
    try:
        new_job.job_status = Job.JobStatus.IN_PROGRESS
        new_job.save()

        LOGGER.info('Zipping directory to an in-memory file ...')
        zipf = BytesIO()
        zipped_bag = zipfile.ZipFile(zipf, 'w', zipfile.ZIP_DEFLATED, False)
        zip_directory(bag.location, zipped_bag)
        zipped_bag.close()
        LOGGER.info('Zipped directory successfully')

        file_name = f'{user_triggered.username}-{bag.bag_name}.zip'
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
        if os.path.exists(bag.location):
            LOGGER.info("Removing bag from disk after zip generation.")
            shutil.rmtree(bag.location)


@django_rq.job
def send_bag_creation_success(form_data: dict, submission: Submission):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    were no errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        submission (Submission): The new submission that was created.
    '''
    subject = 'New Transfer Ready for Review'
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, domain)
    submission_url = 'http://{domain}/{change_url}'.format(
        domain=domain.rstrip(' /'),
        change_url=submission.get_admin_change_url().lstrip(' /')
    )
    LOGGER.info('Generated submission change URL: %s', submission_url)

    recipient_emails = _get_admin_recipient_list(subject)

    user_submitted = submission.user
    send_mail_with_logs(
        recipients=recipient_emails,
        from_email=from_email,
        subject=subject,
        template_name='recordtransfer/email/bag_submit_success.html',
        context={
            'username': user_submitted.username,
            'first_name': user_submitted.first_name,
            'last_name': user_submitted.last_name,
            'action_date': form_data.action_date,
            'submission_url': submission_url,
        }
    )

@django_rq.job
def send_bag_creation_failure(form_data: dict, user_submitted: User):
    ''' Send an email to users who get bag email updates that a user submitted a new bag and there
    WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
    '''
    subject = 'Bag Creation Failed'
    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, domain)

    recipient_emails = _get_admin_recipient_list(subject)

    send_mail_with_logs(
        recipients=recipient_emails,
        from_email=from_email,
        subject=subject,
        template_name='recordtransfer/email/bag_submit_failure.html',
        context={
            'username': user_submitted.username,
            'first_name': user_submitted.first_name,
            'last_name': user_submitted.last_name,
            'action_date': form_data.action_date,
        }
    )

@django_rq.job
def send_thank_you_for_your_transfer(form_data: dict, submission: Submission):
    ''' Send a transfer success email to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        submission (Submission): The new submission that was created.
    '''
    if submission.user.gets_notification_emails:
        domain = Site.objects.get_current().domain
        from_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, domain)

        user_submitted = submission.user
        send_mail_with_logs(
            recipients=[user_submitted.email],
            from_email=from_email,
            subject='Thank You For Your Transfer',
            template_name='recordtransfer/email/transfer_success.html',
            context={
                'archivist_email': settings.ARCHIVIST_EMAIL,
            }
        )

@django_rq.job
def send_your_transfer_did_not_go_through(form_data: dict, user_submitted: User):
    ''' Send a transfer failure email to the user who submitted the transfer.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the transfer form. This is NOT
            the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
    '''
    if user_submitted.gets_notification_emails:
        domain = Site.objects.get_current().domain
        from_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, domain)

        send_mail_with_logs(
            recipients=[user_submitted.email],
            from_email=from_email,
            subject='Issue With Your Transfer',
            template_name='recordtransfer/email/transfer_failure.html',
            context={
                'username': user_submitted.username,
                'first_name': user_submitted.first_name,
                'last_name': user_submitted.last_name,
                'archivist_email': settings.ARCHIVIST_EMAIL,
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
    from_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, domain)

    token = account_activation_token.make_token(new_user)
    LOGGER.info('Generated token for activation link: %s', token)

    send_mail_with_logs(
        recipients=[new_user.email],
        from_email=from_email,
        subject='Activate Your Account',
        template_name='recordtransfer/email/activate_account.html',
        context= {
            'username': new_user.username,
            'base_url': domain,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'token': token,
        }
    )


@django_rq.job
def send_user_account_updated(user_updated: User, context_vars: dict):
    """ Send a notice that the user's account has been updated.

    Args:
        user_updated (User): The user whose account was updated.
        context_vars (dict): Template context variables.
    """

    domain = Site.objects.get_current().domain
    from_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, domain)

    send_mail_with_logs(
        recipients=[user_updated.email],
        from_email=from_email,
        subject=context_vars['subject'],
        template_name='recordtransfer/email/account_updated.html',
        context=context_vars
    )


def send_mail_with_logs(recipients: list, from_email: str, subject, template_name: str,
                        context: dict):
    try:
        if Site.objects.get_current().domain == '127.0.0.1:8000':
            new_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, 'example.com')
            LOGGER.info(
                'Changing FROM email for local development. Using %s instead of %s',
                new_email, from_email
            )
            from_email = new_email
        elif ":" in Site.objects.get_current().domain:
            new_domain = Site.objects.get_current().domain.split(":")[0]
            new_email = '{0}@{1}'.format(settings.DO_NOT_REPLY_USERNAME, new_domain)
            LOGGER.info(
                'Changing FROM email to remove port number. Using {0} instead of {1}',
                new_email, from_email
            )
            from_email = new_email

        LOGGER.info('Setting up new email:')
        LOGGER.info('SUBJECT: %s', subject)
        LOGGER.info('TO: %s', recipients)
        LOGGER.info('FROM: %s', from_email)
        LOGGER.info('Rendering HTML email from %s', template_name)
        context['site_domain'] = Site.objects.get_current().domain
        msg_html = render_to_string(template_name, context)
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
            LOGGER.info('%d emails sent', num_recipients)
    except smtplib.SMTPException as exc:
        LOGGER.error(
            'Error when sending email to user, %s: %s',
            exc.__class__.__name__, str(exc)
        )
