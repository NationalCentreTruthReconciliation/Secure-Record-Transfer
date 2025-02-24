import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.conf import settings

from recordtransfer.emails import send_user_in_progress_submission_expiring
from recordtransfer.models import InProgressSubmission
from recordtransfer.scheduler import schedule_in_progress_submission_expiring_email


class TestInProgressSubmissionExpiringEmailScheduler(unittest.TestCase):
    """Test the in-progress submission expiring email scheduler."""

    @patch("recordtransfer.scheduler.scheduler")
    def test_correct_time_delta_used(self, mock_scheduler: MagicMock) -> None:
        """Test correct time delata is used to schedule email."""
        in_progress = MagicMock(spec=InProgressSubmission)
        in_progress.upload_session = MagicMock()
        in_progress.pk = 1

        settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES = 60
        settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES = 30

        schedule_in_progress_submission_expiring_email(in_progress)

        mock_scheduler.enqueue_in.assert_called_once_with(
            timedelta(minutes=30),
            send_user_in_progress_submission_expiring,
            in_progress.pk,
        )

    @patch("recordtransfer.scheduler.scheduler")
    def test_no_upload_session(
        self, mock_scheduler: MagicMock
    ) -> None:
        """Test scheduling is skipped if there is no upload session associated with the in-progress
        submission.
        """
        in_progress = MagicMock(spec=InProgressSubmission)
        in_progress.upload_session = None

        schedule_in_progress_submission_expiring_email(in_progress)

        mock_scheduler.enqueue_in.assert_not_called()

    @patch("recordtransfer.scheduler.scheduler")
    def test_schedule_in_progress_submission_expiring_email_expiration_disabled_upload_session_expire(
        self, mock_scheduler: MagicMock
    ) -> None:
        """Test scheduling is skipped if expiration settings are disabled for upload session
        expiry.
        """
        in_progress = MagicMock(spec=InProgressSubmission)
        in_progress.upload_session = MagicMock()

        settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES = -1
        settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES = 30

        schedule_in_progress_submission_expiring_email(in_progress)

        mock_scheduler.enqueue_in.assert_not_called()

    @patch("recordtransfer.scheduler.scheduler")
    def test_schedule_in_progress_submission_expiring_email_expiration_disabled_upload_session_reminder(
        self, mock_scheduler: MagicMock
    ) -> None:
        """Test scheduling is skipped if expiration settings are disabled for upload session
        reminder.
        """
        in_progress = MagicMock(spec=InProgressSubmission)
        in_progress.upload_session = MagicMock()

        settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES = 60
        settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES = -1

        schedule_in_progress_submission_expiring_email(in_progress)

        mock_scheduler.enqueue_in.assert_not_called()

