import unittest
from unittest.mock import MagicMock, patch

from recordtransfer.jobs import check_expiring_in_progress_submissions


class TestCheckExpiringInProgressSubmissions(unittest.TestCase):
    """Tests for the check_expiring_in_progress_submissions job."""

    @patch("recordtransfer.jobs.send_user_in_progress_submission_expiring")
    @patch("recordtransfer.models.InProgressSubmission.objects.get_expiring_without_reminder")
    def test_no_expiring_in_progress_submissions(
        self, mock_get_expiring: MagicMock, mock_send_email: MagicMock
    ) -> None:
        """Test when there are no expiring submissions."""
        mock_queryset = MagicMock()
        mock_queryset.count.return_value = 0
        mock_get_expiring.return_value.all.return_value = mock_queryset

        check_expiring_in_progress_submissions()

        mock_send_email.delay.assert_not_called()

    @patch("recordtransfer.jobs.send_user_in_progress_submission_expiring")
    @patch("recordtransfer.models.InProgressSubmission.objects.get_expiring_without_reminder")
    def test_expiring_in_progress_submissions(self, mock_get_expiring: MagicMock, mock_send_email: MagicMock) -> None:
        """Test when there is an expiring submission."""
        mock_in_progress = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.__iter__.return_value = [mock_in_progress]
        mock_queryset.count.return_value = 1
        mock_get_expiring.return_value.all.return_value = mock_queryset

        check_expiring_in_progress_submissions()

        mock_send_email.delay.assert_called_once_with(mock_in_progress)
        mock_in_progress.save.assert_called_once()
        self.assertTrue(mock_in_progress.reminder_email_sent)
