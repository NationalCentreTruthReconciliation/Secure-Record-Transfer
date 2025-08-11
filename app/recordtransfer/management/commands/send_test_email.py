import argparse
import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from recordtransfer.emails import (
    send_password_reset_email,
    send_submission_creation_failure,
    send_submission_creation_success,
    send_thank_you_for_your_submission,
    send_user_account_updated,
    send_user_activation_email,
    send_user_in_progress_submission_expiring,
    send_your_submission_did_not_go_through,
)
from recordtransfer.models import InProgressSubmission, Submission, UploadSession, User

logger = logging.getLogger(__name__)

EMAIL_FUNCTIONS = {
    "submission_creation_success": send_submission_creation_success,
    "submission_creation_failure": send_submission_creation_failure,
    "thank_you_for_your_submission": send_thank_you_for_your_submission,
    "your_submission_did_not_go_through": send_your_submission_did_not_go_through,
    "user_activation_email": send_user_activation_email,
    "user_account_updated": send_user_account_updated,
    "user_in_progress_submission_expiring": send_user_in_progress_submission_expiring,
    "password_reset_email": send_password_reset_email,
}


class Command(BaseCommand):
    """Command to send a test email to a specified address using a given email ID."""

    help = "Send a test email to the specified address using the given email ID."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-line arguments to the parser."""
        parser.add_argument(
            "email_id",
            type=str,
            choices=EMAIL_FUNCTIONS.keys(),
            help="The ID of the email to send (email function name).",
        )
        parser.add_argument(
            "to_email", type=str, help="The email address to send the test email to."
        )

        parser.add_argument(
            "--language",
            "-l",
            type=str,
            choices=[code for code, _ in settings.LANGUAGES],
            help="Optional language code to send the test email in (e.g., 'en', 'fr', 'hi').",
        )

    def handle(self, *args, **options) -> None:
        """Handle the command to send a test email.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments containing 'to_email' and 'email_id'.
        """
        to_email = options["to_email"]
        email_id = options["email_id"]
        language = options.get("language")

        user = self.get_test_user(to_email, language)
        form_data = {"dummy": "data"}
        submission = self.create_test_submission(user)
        in_progress = self.create_test_in_progress_submission(user)

        try:
            self.send_email(email_id, user, form_data, submission, in_progress, language)
            if language:
                logger.info(
                    "✓ Sent '%s' email to %s in language '%s'", email_id, to_email, language
                )
            else:
                logger.info("✓ Sent '%s' email to %s", email_id, to_email)
        except Exception as e:
            logger.exception("Error sending email '%s' to %s: %s", email_id, to_email, e)
            raise CommandError(f"Error sending email: {e}") from e

    def get_test_user(self, email: str, language: Optional[str] = None) -> User:
        """Retrieve or create a test user with the given email address.

        Args:
            email: The email address of the test user.
            language: The language code for the test user.

        Returns:
            User: A User instance that has not been saved to the database.
        """
        return User(
            username="testuser",
            email=email,
            first_name="Test",
            last_name="User",
            is_active=True,
            gets_notification_emails=True,
            gets_submission_email_updates=True,
            language=language or settings.LANGUAGE_CODE,
        )

    def create_test_submission(self, user: User) -> Submission:
        """Create and return a test Submission instance for the given user.

        Args:
            user (User): The user for whom the submission is created.

        Returns:
            Submission: A Submission instance that has not been saved to the database.
        """
        return Submission(user=user, raw_form=b"")

    def create_test_in_progress_submission(self, user: User) -> InProgressSubmission:
        """Create and return a test InProgressSubmission instance for the given user."""
        upload_session = UploadSession(
            started_at=timezone.now(),
            status=UploadSession.SessionStatus.CREATED,
            last_upload_interaction_time=timezone.now() - timedelta(minutes=10),
        )
        return InProgressSubmission(
            user=user,
            title="In-Progress Test",
            upload_session=upload_session,
        )

    def send_email(
        self,
        email_id: str,
        user: User,
        form_data: dict,
        submission: Submission,
        in_progress: InProgressSubmission,
        language: Optional[str] = None,
    ) -> None:
        """Send a test email based on the provided email ID.

        Args:
            email_id (str): The ID of the email to send (email function name).
            user (User): The user object to whom the email is related.
            form_data (dict): Form data to be passed to the email function.
            submission (Submission): A test submission instance.
            in_progress (InProgressSubmission): A test in-progress submission instance.
            language: Optional language code to use for the email.

        Raises:
            CommandError: If no handler is implemented for the given email ID.
        """
        func = EMAIL_FUNCTIONS[email_id]

        test_recipient = ["test@admin.com"]

        if email_id == "submission_creation_success":
            func(form_data, submission, recipient_emails=test_recipient, language=language)
        elif email_id == "submission_creation_failure":
            func(form_data, user, recipient_emails=test_recipient, language=language)
        elif email_id == "thank_you_for_your_submission":
            func(form_data, submission)
        elif email_id == "your_submission_did_not_go_through":
            func(form_data, user)
        elif email_id == "user_activation_email":
            func(user)
        elif email_id == "user_account_updated":
            func(
                user,
                {
                    "subject": _("Account updated"),
                    "changed_item": _("account"),
                    "changed_status": _("updated"),
                    "changed_list": [_("Staff privileges have been added to your account.")],
                },
            )
        elif email_id == "user_in_progress_submission_expiring":
            func(in_progress)
        elif email_id == "password_reset_email":
            func(
                context={
                    "email": user.email,
                    "domain": "example.com",
                    "uid": "dGVzdHVzZXIxMjM=",
                    "user": user,
                    "token": "example-token-123",
                    "protocol": "https",
                },
            )
        else:
            raise CommandError(f"No handler implemented for email_id '{email_id}'")
