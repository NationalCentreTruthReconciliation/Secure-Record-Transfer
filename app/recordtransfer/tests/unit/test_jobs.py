import unittest
from unittest.mock import MagicMock, patch

from recordtransfer.jobs import check_expiring_in_progress_submissions, cleanup_expired_sessions


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
    def test_expiring_in_progress_submissions(
        self, mock_get_expiring: MagicMock, mock_send_email: MagicMock
    ) -> None:
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


class TestCleanupExpiredSessions(unittest.TestCase):
    """Tests for the cleanup_expired_sessions job."""

    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    @patch("recordtransfer.models.UploadSession.objects.get_deletable")
    def test_no_sessions_to_clean_up(
        self, mock_get_expirable: MagicMock, mock_get_deletable: MagicMock
    ) -> None:
        """Test when there are no sessions to clean up."""
        # Set up mocks for empty querysets
        mock_expirable_queryset = MagicMock()
        mock_expirable_queryset.count.return_value = 0
        mock_get_expirable.return_value.all.return_value = mock_expirable_queryset

        mock_deletable_queryset = MagicMock()
        mock_deletable_queryset.count.return_value = 0
        mock_get_deletable.return_value.all.return_value = mock_deletable_queryset

        # Run the job
        cleanup_expired_sessions()

        # Verify the correct methods were called
        mock_get_expirable.assert_called_once()
        mock_get_deletable.assert_called_once()
        # Check that none of the sessions were iterated over, indicating the early return worked
        mock_expirable_queryset.__iter__.assert_not_called()
        mock_deletable_queryset.__iter__.assert_not_called()

    @patch("recordtransfer.models.InProgressSubmission.objects.filter")
    @patch("recordtransfer.models.UploadSession.objects.get_deletable")
    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_expired_session_without_in_progress_submission(
        self, mock_get_expirable: MagicMock, mock_get_deletable: MagicMock, mock_filter: MagicMock
    ) -> None:
        """Test when there's an expired session without an associated in-progress submission."""
        # Setup mocks
        mock_session = MagicMock()

        mock_expirable_queryset = MagicMock()
        mock_expirable_queryset.__iter__.return_value = [mock_session]
        mock_expirable_queryset.count.return_value = 1
        mock_get_expirable.return_value.all.return_value = mock_expirable_queryset

        # Mock that no InProgressSubmission exists for this session
        mock_filter.return_value.exists.return_value = False

        cleanup_expired_sessions()

        # Verify session is deleted
        mock_session.delete.assert_called_once()
        mock_session.remove_uploads.assert_not_called()
        mock_session.expire.assert_not_called()

    @patch("recordtransfer.models.InProgressSubmission.objects.filter")
    @patch("recordtransfer.models.UploadSession.objects.get_deletable")
    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_expired_session_with_in_progress_submission(
        self, mock_get_expirable: MagicMock, mock_get_deletable: MagicMock, mock_filter: MagicMock
    ) -> None:
        """Test when there's an expired session with an associated in-progress submission."""
        # Setup mocks
        mock_session = MagicMock()

        mock_expirable_queryset = MagicMock()
        mock_expirable_queryset.__iter__.return_value = [mock_session]
        mock_expirable_queryset.count.return_value = 1
        mock_get_expirable.return_value.all.return_value = mock_expirable_queryset

        # Mock that an InProgressSubmission exists for this session
        mock_filter.return_value.exists.return_value = True

        cleanup_expired_sessions()

        # Verify uploads are removed and session is expired but not deleted
        mock_session.delete.assert_not_called()
        mock_session.remove_temp_uploads.assert_called_once()
        mock_session.expire.assert_called_once()

    @patch("recordtransfer.models.InProgressSubmission.objects.filter")
    @patch("recordtransfer.models.UploadSession.objects.get_deletable")
    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_expired_session_for_deletion(
        self, mock_get_expirable: MagicMock, mock_get_deletable: MagicMock, mock_filter: MagicMock
    ) -> None:
        """Test when there's an expired session that has been marked for deletion. No files need
        to be removed, since it already has a status of EXPIRED.
        """
        # Setup mocks
        mock_session = MagicMock()

        mock_deletable_queryset = MagicMock()
        mock_deletable_queryset.__iter__.return_value = [mock_session]
        mock_deletable_queryset.count.return_value = 1
        mock_get_deletable.return_value.all.return_value = mock_deletable_queryset

        cleanup_expired_sessions()

        # Verify session is deleted
        mock_session.delete.assert_called_once()
        mock_session.remove_uploads.assert_not_called()
        mock_session.expire.assert_not_called()

    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_exception_handling(self, mock_get_expirable: MagicMock) -> None:
        """Test that exceptions are properly handled."""
        # Setup mock to raise an exception
        mock_get_expirable.side_effect = Exception("Test error")

        # Verify the exception is re-raised
        with self.assertRaises(Exception):
            cleanup_expired_sessions()
