import logging
from datetime import timedelta
import argparse

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from recordtransfer.emails import (
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
}


class Command(BaseCommand):
    help = "Send a test email to the specified address using the given email ID."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-line arguments to the parser."""
        parser.add_argument(
            "to_email", type=str, help="The email address to send the test email to."
        )
        parser.add_argument(
            "email_id",
            type=str,
            choices=EMAIL_FUNCTIONS.keys(),
            help="The ID of the email to send (email function name).",
        )

    def handle(self, *args, **options) -> None:
        """Handle the command to send a test email.

        Args:
            *args: Variable length argument list.
            **options: Arbitrary keyword arguments containing 'to_email' and 'email_id'.
        """
        to_email = options["to_email"]
        email_id = options["email_id"]

        user = self.get_test_user(to_email)
        form_data = {"dummy": "data"}
        submission = self.create_test_submission(user)
        in_progress = self.create_test_in_progress_submission(user)

        try:
            self.send_email(email_id, user, form_data, submission, in_progress)
            logger.info("✅ Sent '%s' email to %s", email_id, to_email)
        except Exception as e:
            logger.exception("Error sending email '%s' to %s: %s", email_id, to_email, e)
            raise CommandError(f"Error sending email: {e}") from e

    def get_test_user(self, email: str) -> User:
        """Retrieve or create a test user with the given email address.

        Args:
            email (str): The email address of the test user.

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
        )

    def create_test_submission(self, user: User) -> Submission:
        """Create and return a test Submission instance for the given user.

        Args:
            user (User): The user for whom the submission is created.

        Returns:
            Submission: A Submission instance that has not been saved to the database.
        """
        return Submission(user=user, raw_form=b"", bag_name="test-bag")

    def create_test_in_progress_submission(self, user: User) -> InProgressSubmission:
        """Create and return a test InProgressSubmission instance for the given user."""
        upload_session = UploadSession.objects.create(
            started_at=timezone.now(),
            status=UploadSession.SessionStatus.CREATED,
            last_upload_interaction_time=timezone.now() - timedelta(minutes=10),
        )
        return InProgressSubmission.objects.create(
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
    ) -> None:
        """Send a test email based on the provided email ID.

        Args:
            email_id (str): The ID of the email to send (email function name).
            user (User): The user object to whom the email is related.
            form_data (dict): Form data to be passed to the email function.
            submission (Submission): A test submission instance.
            in_progress (InProgressSubmission): A test in-progress submission instance.

        Raises:
            CommandError: If no handler is implemented for the given email ID.
        """
        func = EMAIL_FUNCTIONS[email_id]

        if email_id in ("submission_creation_success", "thank_you_for_your_submission"):
            func(form_data, submission)
        elif email_id in ("submission_creation_failure", "your_submission_did_not_go_through"):
            func(form_data, user)
        elif email_id == "user_activation_email":
            func(user)
        elif email_id == "user_account_updated":
            func(user, {
                "subject": "Account updated",
                "changed_item": "account",
                "changed_status": "updated",
                "changed_list": "Staff privileges have been added to your account.",
            })
        elif email_id == "in_progress_submission_expiring":
            func(in_progress)
        else:
            raise CommandError(f"No handler implemented for email_id '{email_id}'")
