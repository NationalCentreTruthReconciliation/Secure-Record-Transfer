import logging
from unittest.mock import MagicMock, patch

from django.test import TestCase

from recordtransfer.enums import SubmissionStep
from recordtransfer.models import (
    InProgressSubmission,
    UploadSession,
    User,
)


class TestInProgressSubmissionSignal(TestCase):
    """Test the signals for the InProgressSubmission model."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        """Set up test."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session(user=self.user)

    @patch.object(UploadSession, "touch")
    def test_touch_called_on_in_progress_submission_save(self, mock_touch: MagicMock) -> None:
        """Test that the upload session's touch method is called when an InProgressSubmission
        instance is saved.
        """
        in_progress_submission = InProgressSubmission(
            upload_session=self.upload_session,
            user=self.upload_session.user,
            current_step=SubmissionStep.UPLOAD_FILES.value,
        )
        in_progress_submission.save()
        mock_touch.assert_called_once()

    @patch.object(InProgressSubmission, "reset_reminder_email_sent")
    def test_reminder_email_sent_flag_updated(self, mock_reset: MagicMock) -> None:
        """Test that the reminder email sent flag is updated when the InProgressSubmission instance
        is saved.
        """
        in_progress_submission = InProgressSubmission(
            upload_session=self.upload_session,
            user=self.upload_session.user,
            current_step=SubmissionStep.UPLOAD_FILES.value,
            reminder_email_sent=True,
        )
        in_progress_submission.save()
        mock_reset.assert_called_once()
