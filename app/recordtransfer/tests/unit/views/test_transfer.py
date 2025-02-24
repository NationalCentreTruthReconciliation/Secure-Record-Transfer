from typing import cast
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase
from django.urls import reverse

from recordtransfer.models import InProgressSubmission, UploadSession, User
from recordtransfer.views.transfer import TransferFormWizard


class TransferFormWizardTests(TestCase):
    """Tests for the TransferFormWizard view."""

    def setUp(self) -> None:
        """Set up the test case with a user and an in-progress submission."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.upload_session = UploadSession.new_session(user=cast(User, self.user))
        self.in_progress_submission = InProgressSubmission.objects.create(
            user=self.user,
            uuid="550e8400-e29b-41d4-a716-446655440000",
            upload_session=self.upload_session,
        )

    @patch("recordtransfer.models.UploadSession.expired", new_callable=MagicMock)
    @patch("recordtransfer.views.transfer.TransferFormWizard.get")
    def test_resume_in_progress_submission_redirects_to_submission_expired(
        self, mock_get: MagicMock, mock_expired: MagicMock
    ) -> None:
        """Test that the view redirects to the submission expired page if the in-progress
        submission is expired.
        """
        mock_expired.return_value = True

        request = self.factory.get(
            reverse("recordtransfer:transfer"),
            {"transfer_uuid": "550e8400-e29b-41d4-a716-446655440000"},
        )
        request.user = self.user

        response = TransferFormWizard.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("recordtransfer:in_progress_submission_expired"))
