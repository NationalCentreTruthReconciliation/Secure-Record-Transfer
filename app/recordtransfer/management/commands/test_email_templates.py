import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from recordtransfer.models import User, Submission, InProgressSubmission, UploadSession
from recordtransfer.emails import (
    send_submission_creation_success,
    send_submission_creation_failure,
    send_thank_you_for_your_submission,
    send_your_submission_did_not_go_through,
    send_user_activation_email,
    send_user_account_updated,
    send_user_in_progress_submission_expiring,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test all email sending functions."

    def handle(self, *args, **options):
        user = self.create_test_user()
        form_data = {"dummy": "data"}
        submission = self.create_test_submission(user)
        in_progress = self.create_test_in_progress_submission(user)

        self.send_all_emails(user, form_data, submission, in_progress)

    def create_test_user(self):
        user, _ = User.objects.get_or_create(
            username="testuser",
            defaults={
                "email": "testuser@example.com",
                "first_name": "Test",
                "last_name": "User",
                "is_active": True,
                "gets_notification_emails": True,
                "gets_submission_email_updates": True,
            },
        )
        return user

    def create_test_submission(self, user):
        return Submission.objects.create(
            user=user,
            raw_form=b"",
            bag_name="test-bag",
        )

    def create_test_in_progress_submission(self, user):
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

    def send_all_emails(self, user, form_data, submission, in_progress):
        logger.info("Sending all test emails...")
        send_submission_creation_success(form_data, submission)
        logger.info("✔ Sent: submission_creation_success")
        send_submission_creation_failure(form_data, user)
        logger.info("✔ Sent: submission_creation_failure")
        send_thank_you_for_your_submission(form_data, submission)
        logger.info("✔ Sent: thank_you_for_your_submission")
        send_your_submission_did_not_go_through(form_data, user)
        logger.info("✔ Sent: your_submission_did_not_go_through")
        send_user_activation_email(user)
        logger.info("✔ Sent: user_activation_email")
        send_user_account_updated(user, {"subject": "Your Account Was Updated"})
        logger.info("✔ Sent: user_account_updated")
        send_user_in_progress_submission_expiring(in_progress)
        logger.info("✔ Sent: in_progress_submission_expiring")
        logger.info("✅ All test emails sent.")
