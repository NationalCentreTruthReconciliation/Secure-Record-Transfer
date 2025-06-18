"""Email notifications sent by recordtransfer application."""

import logging
import re
import smtplib
from typing import List

import django_rq
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from recordtransfer.enums import SiteSettingKey
from recordtransfer.models import InProgressSubmission, SiteSetting, Submission, User
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import html_to_text

LOGGER = logging.getLogger("rq.worker")

__all__ = [
    "send_submission_creation_success",
    "send_submission_creation_failure",
    "send_thank_you_for_your_submission",
    "send_your_submission_did_not_go_through",
    "send_user_activation_email",
    "send_user_account_updated",
]


@django_rq.job
def send_submission_creation_success(form_data: dict, submission: Submission) -> None:
    """Send an email to users who get submission email updates that a user submitted a new
    submission and there were no errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the submission form. This is
            NOT the CAAIS tree version of the form.
        submission (Submission): The new submission that was created.
    """
    subject = "New Submission Ready for Review"

    domain = Site.objects.get_current().domain
    submission_url = "http://{domain}/{change_url}".format(
        domain=domain.rstrip(" /"), change_url=submission.get_admin_change_url().lstrip(" /")
    )
    LOGGER.info("Generated submission change URL: %s", submission_url)

    recipient_emails = _get_admin_recipient_list(subject)

    user_submitted = submission.user
    _send_mail_with_logs(
        recipients=recipient_emails,
        from_email=_get_do_not_reply_email_address(),
        subject=subject,
        template_name="recordtransfer/email/submission_submit_success.html",
        context={
            "username": user_submitted.username,
            "first_name": user_submitted.first_name,
            "last_name": user_submitted.last_name,
            "action_date": submission.submission_date,
            "submission_url": submission_url,
            "base_url": Site.objects.get_current().domain,
        },
    )


@django_rq.job
def send_submission_creation_failure(form_data: dict, user_submitted: User) -> None:
    """Send an email to users who get submission email updates that a user submitted a new
    submission and there WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the submission form. This is
            NOT the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
    """
    subject = "Submission Failed"
    recipient_emails = _get_admin_recipient_list(subject)

    _send_mail_with_logs(
        recipients=recipient_emails,
        from_email=_get_do_not_reply_email_address(),
        subject=subject,
        template_name="recordtransfer/email/submission_submit_failure.html",
        context={
            "username": user_submitted.username,
            "first_name": user_submitted.first_name,
            "last_name": user_submitted.last_name,
            "action_date": timezone.now(),
            "base_url": Site.objects.get_current().domain,
        },
    )


@django_rq.job
def send_thank_you_for_your_submission(form_data: dict, submission: Submission) -> None:
    """Send a submission success email to the user who made the submission.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the submission form. This is NOT
            the CAAIS tree version of the form.
        submission (Submission): The new submission that was created.
    """
    if submission.user.gets_notification_emails:
        _send_mail_with_logs(
            recipients=[submission.user.email],
            from_email=_get_do_not_reply_email_address(),
            subject="Thank You For Your Submission",
            template_name="recordtransfer/email/submission_success.html",
            context={
                "archivist_email": SiteSetting.get_value_str(SiteSettingKey.ARCHIVIST_EMAIL),
            },
        )


@django_rq.job
def send_your_submission_did_not_go_through(form_data: dict, user_submitted: User) -> None:
    """Send a submission failure email to the user who made the submission.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the submission form. This is
            NOT the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
    """
    if user_submitted.gets_notification_emails:
        _send_mail_with_logs(
            recipients=[user_submitted.email],
            from_email=_get_do_not_reply_email_address(),
            subject="Issue With Your Submission",
            template_name="recordtransfer/email/submission_failure.html",
            context={
                "username": user_submitted.username,
                "first_name": user_submitted.first_name,
                "last_name": user_submitted.last_name,
                "archivist_email": SiteSetting.get_value_str(SiteSettingKey.ARCHIVIST_EMAIL),
            },
        )


@django_rq.job
def send_user_activation_email(new_user: User) -> None:
    """Send an activation email to the new user who is attempting to create an account. The user
    must visit the link to activate their account.

    Args:
        new_user (User): The new user who requested an account
    """
    token = account_activation_token.make_token(new_user)
    LOGGER.info("Generated token for activation link: %s", token)

    _send_mail_with_logs(
        recipients=[new_user.email],
        from_email=_get_do_not_reply_email_address(),
        subject="Activate Your Account",
        template_name="recordtransfer/email/activate_account.html",
        context={
            "username": new_user.username,
            "base_url": Site.objects.get_current().domain,
            "uid": urlsafe_base64_encode(force_bytes(new_user.pk)),
            "token": token,
        },
    )


@django_rq.job
def send_user_account_updated(user_updated: User, context_vars: dict) -> None:
    """Send a notice that the user's account has been updated.

    Args:
        user_updated (User): The user whose account was updated.
        context_vars (dict): Template context variables.
    """
    _send_mail_with_logs(
        recipients=[user_updated.email],
        from_email=_get_do_not_reply_email_address(),
        subject=context_vars["subject"],
        template_name="recordtransfer/email/account_updated.html",
        context=context_vars,
    )


@django_rq.job
def send_user_in_progress_submission_expiring(in_progress: InProgressSubmission) -> None:
    """Send an email to a user that their in-progress submission is expiring soon.

    Args:
         in_progress: The in-progress submission to remind the user about
    """
    _send_mail_with_logs(
        recipients=[in_progress.user.email],
        from_email=_get_do_not_reply_email_address(),
        subject="Your In-Progress Submission is Expiring Soon",
        template_name="recordtransfer/email/in_progress_submission_expiring.html",
        context={
            "username": in_progress.user.username,
            "full_name": in_progress.user.get_full_name(),
            "base_url": Site.objects.get_current().domain,
            "in_progress_title": in_progress.title,
            "in_progress_expiration_date": timezone.localtime(
                in_progress.upload_session_expires_at
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "in_progress_url": in_progress.get_resume_url(),
        },
    )


def _get_admin_recipient_list(subject: str) -> List[str]:
    """Get a list of admin users who are set up to receive notification emails.

    Args:
        subject (str): The subject of the email

    Returns:
        (List[str]): A list of email addresses
    """
    LOGGER.info('Finding Users to send "%s" email to', subject)
    recipients_list = list(
        User.objects.filter(gets_submission_email_updates=True, is_staff=True).values_list(
            "email", flat=True
        )
    )

    if not recipients_list:
        LOGGER.warning("There are no users configured to receive submission update emails.")
        return []
    LOGGER.info(
        "Found %d Users(s) to send email to: %s", len(recipients_list), str(recipients_list)
    )
    return recipients_list


def _get_do_not_reply_email_address() -> str:
    """Get a do not reply email address using the current site's domain and the
    DO_NOT_REPLY_USERNAME site setting.
    """
    domain = Site.objects.get_current().domain
    matched = re.match(r"^(?P<domain>[^:]+)(?::(?P<port>\d+))?$", domain)

    if matched and matched.group("domain").lower() in ("127.0.0.1", "localhost"):
        clean_domain = "example.com"
        LOGGER.info(
            "Changing FROM email for local development. Using %s instead of %s",
            clean_domain,
            domain,
        )

    elif matched and matched.group("port") is not None:
        clean_domain = matched.group("domain")
        LOGGER.info(
            "Changing FROM email to remove port number. Using %s instead of %s",
            clean_domain,
            domain,
        )

    else:
        clean_domain = domain

    return f"{SiteSetting.get_value_str(SiteSettingKey.DO_NOT_REPLY_USERNAME)}@{clean_domain}"


def _send_mail_with_logs(
    recipients: List[str], from_email: str, subject: str, template_name: str, context: dict
):
    """Send an HTML email and a Text email, while logging what is being sent.

    Args:
        recipients (List[str]): A list of recipients to receive this email
        from_email (str): A "From" address to send the email as
        subject (str): A subject for the email
        template_name (str): The name of the email template
        context (dict): Any context that may need to be used to render the email
    """
    try:
        LOGGER.info("Setting up new email:")
        LOGGER.info("SUBJECT: %s", subject)
        LOGGER.info("TO: %s", recipients)
        LOGGER.info("FROM: %s", from_email)
        LOGGER.info("Rendering HTML email from %s", template_name)
        context["site_domain"] = Site.objects.get_current().domain
        msg_html = render_to_string(template_name, context)
        LOGGER.info("Stripping tags from rendered HTML to create a plaintext email")
        msg_plain = html_to_text(msg_html)
        LOGGER.info("Sending...")
        send_mail(
            subject=subject,
            message=msg_plain,
            from_email=from_email,
            recipient_list=recipients,
            html_message=msg_html,
            fail_silently=False,
        )
        num_recipients = len(recipients)
        if num_recipients == 1:
            LOGGER.info("1 email sent")
        else:
            LOGGER.info("%d emails sent", num_recipients)
    except smtplib.SMTPException as exc:
        LOGGER.error("Error when sending email to user, %s: %s", exc.__class__.__name__, str(exc))
