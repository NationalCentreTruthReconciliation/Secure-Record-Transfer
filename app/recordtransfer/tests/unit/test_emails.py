from unittest.mock import MagicMock, PropertyMock, patch

from django.test import TestCase

from recordtransfer.emails import send_user_in_progress_submission_expiring
from recordtransfer.enums import TransferStep
from recordtransfer.models import InProgressSubmission, UploadSession, User


class TestSendUserInProgressSubmissionExpiring(TestCase):
    """Test the send_user_in_progress_submission_expiring function."""

    def setUp(self) -> None:
        """Set up before each test."""
        self.user = User.objects.create(
            username="testuser", email="test@example.com", first_name="Test", last_name="User"
        )
        self.session = UploadSession.new_session(user=self.user)
        self.in_progress = InProgressSubmission.objects.create(
            user=self.user,
            current_step=TransferStep.UPLOAD_FILES.value,
            title="Test Submission",
            upload_session=self.session,
        )

    def tearDown(self) -> None:
        """Clean up after each test."""
        UploadSession.objects.all().delete()
        InProgressSubmission.objects.all().delete()
        User.objects.all().delete()

    @patch("recordtransfer.emails._send_mail_with_logs")
    def test_send_email_when_in_progress_expiring_soon(self, mock_send_mail: MagicMock) -> None:
        """Test email is sent when in-progress submission's upload session is expiring soon."""
        with patch.object(
            InProgressSubmission,
            "upload_session_expires_soon",
            new_callable=PropertyMock,
            return_value=True,
        ):
            send_user_in_progress_submission_expiring(self.in_progress.pk)

        mock_send_mail.assert_called_once()

    @patch("recordtransfer.emails._send_mail_with_logs")
    def test_no_email_when_in_progress_not_expiring_soon(self, mock_send_mail: MagicMock) -> None:
        """Test no email is sent when in-progress submission's upload session is not expiring
        soon.
        """
        with patch.object(
            InProgressSubmission,
            "upload_session_expires_soon",
            new_callable=PropertyMock,
            return_value=False,
        ):
            send_user_in_progress_submission_expiring(self.in_progress.pk)

        mock_send_mail.assert_not_called()

    @patch("recordtransfer.emails._send_mail_with_logs")
    def test_no_email_when_in_progress_submission_not_found(
        self, mock_send_mail: MagicMock
    ) -> None:
        """Test no email is sent given an invalid in-progress submission primary key."""
        non_existent_pk = 99999
        send_user_in_progress_submission_expiring(non_existent_pk)

        mock_send_mail.assert_not_called()

    @patch("recordtransfer.emails._send_mail_with_logs")
    def test_no_email_when_in_progress_submission_deleted(self, mock_send_mail: MagicMock) -> None:
        """Test no email is sent when in-progress submission is deleted, which happens if an
        InProgresSubmission has been made into a complete Submission or if it is manually deleted
        by a user/admin.
        """
        self.in_progress.delete()
        send_user_in_progress_submission_expiring(self.in_progress.pk)

        mock_send_mail.assert_not_called()

    @patch("recordtransfer.emails._send_mail_with_logs")
    def test_no_email_when_no_expiration_date(self, mock_send_mail: MagicMock) -> None:
        """Test no email is sent when in-progress submission has no expiration date."""
        with patch.object(
            InProgressSubmission,
            "upload_session_expires_soon",
            new_callable=PropertyMock,
            return_value=True,
        ) and patch.object(
            InProgressSubmission,
            "upload_session_expires_at",
            new_callable=PropertyMock,
            return_value=None,
        ):
            send_user_in_progress_submission_expiring(self.in_progress.pk)

        mock_send_mail.assert_not_called()

    @patch("recordtransfer.emails._send_mail_with_logs")
    def test_email_context_contains_correct_data(self, mock_send_mail: MagicMock) -> None:
        """Test email context contains all required fields."""
        with patch.object(InProgressSubmission, "upload_session_expires_soon", return_value=True):
            send_user_in_progress_submission_expiring(self.in_progress.pk)

        mock_send_mail.assert_called_once()
        context = mock_send_mail.call_args[1]["context"]

        self.assertEqual(context["username"], self.user.username)
        self.assertEqual(context["full_name"], self.user.get_full_name())
        self.assertEqual(context["in_progress_title"], self.in_progress.title)
        self.assertTrue("in_progress_expiration_date" in context)
        self.assertTrue("in_progress_url" in context)
