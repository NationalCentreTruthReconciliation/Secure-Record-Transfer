import logging
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from recordtransfer.enums import TransferStep
from recordtransfer.models import (
    InProgressSubmission,
    PermUploadedFile,
    TempUploadedFile,
    UploadSession,
    User,
)


class TestUploadedFileSignal(TestCase):
    """Test the signals for the uploaded file (TempUploadedFile, PermUploadedFile) models."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        """Set up test."""
        self.session = UploadSession.new_session()
        self.test_file = SimpleUploadedFile(
            "test1.pdf", b"Test file content", content_type="application/pdf"
        )

    @patch("django.core.files.storage.FileSystemStorage.delete")
    def test_file_deleted_on_temp_file_delete(self, mock_delete: MagicMock) -> None:
        """Test that the file is deleted when the TempUploadedFile model instance is deleted."""
        temp_uploaded_file = TempUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        temp_uploaded_file.save()
        temp_uploaded_file.delete()
        mock_delete.assert_called_once()

    @patch("django.core.files.storage.FileSystemStorage.delete")
    def test_file_deleted_on_perm_file_delete(self, mock_delete: MagicMock) -> None:
        """Test that the file is deleted when the PermUploadedFile model instance is deleted."""
        perm_uploaded_file = PermUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        perm_uploaded_file.save()
        perm_uploaded_file.delete()
        mock_delete.assert_called_once()

    @patch.object(UploadSession, "touch")
    def test_upload_session_touch_called_on_temp_file_deletion(
        self, mock_touch: MagicMock
    ) -> None:
        """Test that the upload session's touch method is called when a TempUploadedFile model
        instance is deleted.
        """
        temp_uploaded_file = TempUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        temp_uploaded_file.save()
        temp_uploaded_file.delete()
        mock_touch.assert_called_once()

    @patch.object(UploadSession, "touch")
    def test_upload_session_touch_not_called_on_perm_file_deletion(
        self, mock_touch: MagicMock
    ) -> None:
        """Test that the upload session's touch method is not called when a PermUploadedFile model
        instance is deleted.
        """
        perm_uploaded_file = PermUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        perm_uploaded_file.save()
        perm_uploaded_file.delete()
        mock_touch.assert_not_called()


class TestInProgressSubmissionSignal(TestCase):
    """Test the signals for the InProgressSubmission model."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @patch.object(UploadSession, "touch")
    def test_touch_called_on_in_progress_submission_save(self, mock_touch: MagicMock) -> None:
        """Test that the upload session's touch method is called when an InProgressSubmission
        instance is saved.
        """
        # Create upload session
        user = User.objects.create(username="testuser", password="password")
        upload_session = UploadSession.new_session(user=user)

        # Create and save an InProgressSubmission with the upload session
        in_progress_submission = InProgressSubmission(
            upload_session=upload_session,
            user=upload_session.user,
            current_step=TransferStep.UPLOAD_FILES.value,
        )
        in_progress_submission.save()

        # Verify touch() was called once
        mock_touch.assert_called_once()
