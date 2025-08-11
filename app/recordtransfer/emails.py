"""Email notifications sent by recordtransfer application."""

import logging
import re
import smtplib
from collections import defaultdict
from typing import List, Optional

import django_rq
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from recordtransfer.enums import SiteSettingKey
from recordtransfer.models import InProgressSubmission, SiteSetting, Submission, User
from recordtransfer.tokens import account_activation_token
from recordtransfer.utils import html_to_text

LOGGER = logging.getLogger(__name__)


def _get_base_url_with_protocol() -> str:
    """Get the base URL with the appropriate protocol for the current environment.

    Returns:
        str: Full base URL with protocol (e.g., 'http://localhost:8000' or 'https://example.com')
    """
    # In development, use EMAIL_BASE_URL setting
    if settings.DEBUG:
        return settings.EMAIL_BASE_URL

    # In production, use HTTPS with the actual domain
    domain = Site.objects.get_current().domain
    return f"https://{domain}"


__all__ = [
    "send_password_reset_email",
    "send_submission_creation_failure",
    "send_submission_creation_success",
    "send_thank_you_for_your_submission",
    "send_user_account_updated",
    "send_user_activation_email",
    "send_your_submission_did_not_go_through",
]


@django_rq.job
def send_submission_creation_success(
    form_data: dict,
    submission: Submission,
    recipient_emails: Optional[List[str]] = None,
    language: Optional[str] = None,
) -> None:
    """Send an email to users who get submission email updates that a user submitted a new
    submission and there were no errors.

    Args:
        form_data: A dictionary of the cleaned form data from the submission form. This is
            NOT the CAAIS tree version of the form.
        submission: The new submission that was created.
        recipient_emails: Optional list of recipient emails. If provided, overrides the default
            admin recipients.
        language: Optional language code to use for rendering the email. Only used when
            `recipient_emails` is provided.
    """

    subject = "New Submission Ready for Review"

    submission_url = f"{_get_base_url_with_protocol().rstrip('/')}/{submission.get_admin_change_url().lstrip('/')}"
    LOGGER.info("Generated submission change URL: %s", submission_url)

    user_submitted = submission.user
    if not user_submitted:
        LOGGER.error(
            "Submission %d has no associated user. Cannot send submission creation success email.",
            submission.pk,
        )
        return

    # Send to admin recipients grouped by language or use provided recipients with language
    if recipient_emails:
        # For testing or custom recipients, use the specified language or default
        target_language = language or translation.get_language()
        recipients = {target_language: recipient_emails}
    else:
        # Use the default admin recipients grouped by their language preferences
        recipients = _get_emails_grouped_by_lang(
            list(User.objects.filter(gets_submission_email_updates=True, is_staff=True))
        )

    if not recipients:
        LOGGER.warning("No recipients found for submission creation success email. Skipping send.")
        return

    _send_mail_by_language_groups(
        recipients=recipients,
        from_email=_get_do_not_reply_email_address(),
        subject=_("New Submission Ready for Review"),
        template_name="recordtransfer/email/submission_submit_success.html",
        context={
            "username": user_submitted.username,
            "first_name": user_submitted.first_name,
            "last_name": user_submitted.last_name,
            "action_date": submission.submission_date,
            "submission_url": submission_url,
        },
    )


@django_rq.job
def send_submission_creation_failure(
    form_data: dict,
    user_submitted: User,
    recipient_emails: Optional[List[str]] = None,
    language: Optional[str] = None,
) -> None:
    """Send an email to users who get submission email updates that a user submitted a new
    submission and there WERE errors.

    Args:
        form_data (dict): A dictionary of the cleaned form data from the submission form. This is
            NOT the CAAIS tree version of the form.
        user_submitted (User): The user that tried to create the submission.
        recipient_emails: Optional list of recipient emails. If provided, overrides the default
            admin recipients.
        language: Optional language code to use for rendering the email. Only used when
            `recipient_emails` is provided.
    """
    # Send to admin recipients grouped by language or use provided recipients with language
    if recipient_emails:
        # For testing or custom recipients, use the specified language or default
        target_language = language or translation.get_language()
        recipients = {target_language: recipient_emails}
    else:
        # Use the default admin recipients grouped by their language preferences
        recipients = _get_emails_grouped_by_lang(
            list(User.objects.filter(gets_submission_email_updates=True, is_staff=True))
        )

    if not recipients:
        LOGGER.warning("No recipients found for submission creation failure email. Skipping send.")
        return

    _send_mail_by_language_groups(
        recipients=recipients,
        from_email=_get_do_not_reply_email_address(),
        subject=_("Submission Failed"),
        template_name="recordtransfer/email/submission_submit_failure.html",
        context={
            "username": user_submitted.username,
            "first_name": user_submitted.first_name,
            "last_name": user_submitted.last_name,
            "action_date": timezone.now(),
        },
    )


@django_rq.job
def send_thank_you_for_your_submission(form_data: dict, submission: Submission) -> None:
    """Send a submission success email to the user who made the submission.

    Args:
        form_data: A dictionary of the cleaned form data from the submission form.
            This is NOT the CAAIS tree version of the form.
        submission: The new submission that was created.
    """
    user_submitted = submission.user
    if not user_submitted:
        LOGGER.error(
            "Submission %d has no associated user. Cannot send thank you for your submission email.",
            submission.pk,
        )
        return
    if user_submitted.gets_notification_emails:
        _send_mail(
            recipient=user_submitted.email,
            from_email=_get_do_not_reply_email_address(),
            subject=_("Thank You For Your Submission"),
            template_name="recordtransfer/email/submission_success.html",
            context={
                "archivist_email": SiteSetting.get_value_str(SiteSettingKey.ARCHIVIST_EMAIL),
            },
            user_language=user_submitted.language,
        )


@django_rq.job
def send_your_submission_did_not_go_through(form_data: dict, user_submitted: User) -> None:
    """Send a submission failure email to the user who made the submission.

    Args:
        form_data: A dictionary of the cleaned form data from the submission form. This is
            NOT the CAAIS tree version of the form.
        user_submitted: The user that tried to create the submission.
    """
    if user_submitted.gets_notification_emails:
        _send_mail(
            recipient=user_submitted.email,
            from_email=_get_do_not_reply_email_address(),
            subject=_("Issue With Your Submission"),
            template_name="recordtransfer/email/submission_failure.html",
            context={
                "username": user_submitted.username,
                "first_name": user_submitted.first_name,
                "last_name": user_submitted.last_name,
                "archivist_email": SiteSetting.get_value_str(SiteSettingKey.ARCHIVIST_EMAIL),
            },
            user_language=user_submitted.language,
        )


@django_rq.job
def send_user_activation_email(new_user: User) -> None:
    """Send an activation email to the new user who is attempting to create an account. The user
    must visit the link to activate their account.

    Args:
        new_user: The new user who requested an account
    """
    token = account_activation_token.make_token(new_user)
    LOGGER.info("Generated token for activation link: %s", token)

    _send_mail(
        recipient=new_user.email,
        from_email=_get_do_not_reply_email_address(),
        subject=_("Activate Your Account"),
        template_name="recordtransfer/email/activate_account.html",
        context={
            "username": new_user.username,
            "uid": urlsafe_base64_encode(force_bytes(new_user.pk)),
            "token": token,
        },
        user_language=new_user.language,
    )


@django_rq.job
def send_user_account_updated(user_updated: User, context_vars: dict) -> None:
    """Send a notice that the user's account has been updated.

    Args:
        user_updated: The user whose account was updated.
        context_vars: Template context variables.
    """
    _send_mail(
        recipient=user_updated.email,
        from_email=_get_do_not_reply_email_address(),
        subject=context_vars["subject"],
        template_name="recordtransfer/email/account_updated.html",
        context=context_vars,
        user_language=user_updated.language,
    )


@django_rq.job
def send_user_in_progress_submission_expiring(in_progress: InProgressSubmission) -> None:
    """Send an email to a user that their in-progress submission is expiring soon.

    Args:
         in_progress: The in-progress submission to remind the user about
    """
    _send_mail(
        recipient=in_progress.user.email,
        from_email=_get_do_not_reply_email_address(),
        subject=_("Your In-Progress Submission is Expiring Soon"),
        template_name="recordtransfer/email/in_progress_submission_expiring.html",
        context={
            "username": in_progress.user.username,
            "full_name": in_progress.user.full_name,
            "in_progress_title": in_progress.title,
            "in_progress_expiration_date": timezone.localtime(
                in_progress.upload_session_expires_at
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "in_progress_url": in_progress.get_resume_url(),
        },
        user_language=in_progress.user.language,
    )


@django_rq.job
def send_password_reset_email(
    context: dict,
) -> None:
    """Send a password reset email asynchronously using django_rq.

    Args:
        context: Context variables for the email, including:
            - email: The recipient's email address
            - user: The User object for the recipient
    """
    to_email = context.get("email")

    if not to_email:
        LOGGER.error("Missing email in context for password reset email.")
        return

    _send_mail(
        recipient=to_email,
        from_email=_get_do_not_reply_email_address(),
        subject=_("Password Reset on NCTR Record Transfer Portal"),
        template_name="registration/password_reset_email.html",
        context=context,
    )


def _get_emails_grouped_by_lang(users: list[User]) -> dict[str, List[str]]:
    """Get a dictionary of user emails grouped by their language preferences for notification
    emails.

    Args:
        users: A list of User objects to group by language.

    Returns:
        A dictionary with language codes as keys and lists of email addresses as values.
    """
    language_groups = defaultdict(list)
    for user in users:
        lang_key = user.language or translation.get_language()
        language_groups[lang_key].append(user.email)
    return language_groups


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


def _send_mail(
    recipient: str,
    from_email: str,
    subject: str,
    template_name: str,
    context: dict,
    user_language: Optional[str] = None,
) -> None:
    """Send an HTML email and a Text email to a recipient.

    Args:
        recipient: A recipient email address
        from_email: A "From" address to send the email as
        subject: A subject for the email
        template_name: The name of the email template
        context: Any context that may need to be used to render the email
        user_language: The language to use for the email
    """
    try:
        LOGGER.info("Setting up new email:")
        LOGGER.info("SUBJECT: %s", subject)
        LOGGER.info("TO: %s", recipient)
        LOGGER.info("FROM: %s", from_email)
        context["base_url"] = _get_base_url_with_protocol()
        context["site_domain"] = Site.objects.get_current().domain

        with translation.override(user_language or translation.get_language()):
            msg_html = render_to_string(template_name, context)
            LOGGER.info("Stripping tags from rendered HTML to create a plaintext email")
            msg_plain = html_to_text(msg_html)

            LOGGER.info("Sending...")
            send_mail(
                subject=subject,
                message=msg_plain,
                from_email=from_email,
                recipient_list=[recipient],
                html_message=msg_html,
                fail_silently=False,
            )

            LOGGER.info("Email sent")

    except smtplib.SMTPException as exc:
        LOGGER.error("Error when sending email to user, %s: %s", exc.__class__.__name__, str(exc))


def _send_mail_by_language_groups(
    recipients: dict[str, List[str]],
    from_email: str,
    subject: str,
    template_name: str,
    context: dict,
) -> None:
    """Send an HTML email and a Text email to recipients grouped by language.

    Args:
        recipients: A dictionary mapping language codes to lists of recipients
        from_email: A "From" address to send the email as
        subject: A subject for the email
        template_name: The name of the email template
        context: Any context that may need to be used to render the email.
    """
    try:
        LOGGER.info("Setting up new email:")
        LOGGER.info("SUBJECT: %s", subject)
        LOGGER.info("TO (by language): %s", recipients)
        LOGGER.info("FROM: %s", from_email)
        context["base_url"] = _get_base_url_with_protocol()

        for lang, recipient_list in recipients.items():
            if not recipient_list:
                continue

            current_language = lang or translation.get_language()
            LOGGER.info("Rendering email for language: %s", current_language)
            LOGGER.info("Recipients for language %s: %s", current_language, recipient_list)

            with translation.override(current_language):
                msg_html = render_to_string(template_name, context)
                LOGGER.info("Stripping tags from rendered HTML to create a plaintext email")
                msg_plain = html_to_text(msg_html)

                LOGGER.info("Sending...")
                send_mail(
                    subject=subject,
                    message=msg_plain,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    html_message=msg_html,
                    fail_silently=False,
                )

                num_recipients = len(recipient_list)
                if num_recipients == 1:
                    LOGGER.info("1 email sent for language %s", current_language)
                else:
                    LOGGER.info("%d emails sent for language %s", num_recipients, current_language)

    except smtplib.SMTPException as exc:
        LOGGER.error("Error when sending email to user, %s: %s", exc.__class__.__name__, str(exc))
