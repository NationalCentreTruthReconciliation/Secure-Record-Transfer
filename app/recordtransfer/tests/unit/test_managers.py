from datetime import timezone as dttimezone
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from recordtransfer.enums import SubmissionStep
from recordtransfer.models import InProgressSubmission, UploadSession, User


class TestInProgressSubmissionManager(TestCase):
    """Tests for the InProgressSubmission manager."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session(user=self.user)
        self.in_progress_submission = InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=SubmissionStep.UPLOAD_FILES.value,
        )

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 10)
    def test_one_expiring(self, mock_now: MagicMock) -> None:
        """Test when there is an expiring submission."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=(
                settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
                - settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
            )
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertIn(self.in_progress_submission, expiring_submissions)

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 10)
    def test_none_expiring(self, mock_now: MagicMock) -> None:
        """Test when there are no expiring submissions."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=(
                settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
                - settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
            )
        )

        # Set last upload interaction time to be greater than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time + timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertFalse(expiring_submissions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", -1)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 10)
    def test_upload_session_expiry_disabled(self, mock_now: MagicMock) -> None:
        """Test when the upload session expiry feature is disabled."""
        # Test get_expiring method
        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertFalse(expiring_submissions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", -1)
    def test_upload_session_expiry_reminder_disabled(self, mock_now: MagicMock) -> None:
        """Test when the upload session expiry reminder feature is disabled."""
        # Test get_expiring method
        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertFalse(expiring_submissions.exists())
