import logging
import os

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

    def test_file_exists_on_temp_file_creation(self) -> None:
        """Test that the file exists when a TempUploadedFile model instance is created."""
        temp_uploaded_file = TempUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        temp_uploaded_file.save()
        self.assertTrue(os.path.exists(temp_uploaded_file.file_upload.path))

    def test_file_deleted_on_temp_file_delete(self) -> None:
        """Test that the file is deleted when the TempUploadedFile model instance is deleted."""
        temp_uploaded_file = TempUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        temp_uploaded_file.save()
        file_path = temp_uploaded_file.file_upload.path
        temp_uploaded_file.delete()
        self.assertFalse(os.path.exists(file_path))

    def test_file_exist_on_perm_file_creation(self) -> None:
        """Test that the file exists when a PermUploadedFile model instance is created."""
        perm_uploaded_file = PermUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        perm_uploaded_file.save()
        self.assertTrue(os.path.exists(perm_uploaded_file.file_upload.path))

    def test_file_deleted_on_perm_file_delete(self) -> None:
        """Test that the file is deleted when the PermUploadedFile model instance is deleted."""
        perm_uploaded_file = PermUploadedFile(
            name="test.pdf", session=self.session, file_upload=self.test_file
        )
        perm_uploaded_file.save()
        file_path = perm_uploaded_file.file_upload.path
        perm_uploaded_file.delete()
        self.assertFalse(os.path.exists(file_path))

class TestInProgressSubmissionSignal(TestCase):
    """Test the signals for the InProgressSubmission model."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def test_touch_called_on_in_progress_submission_save(self) -> None:
        """Test that the upload session's touch method is called when an InProgressSubmission
        model instance is saved.
        """
        # Create initial upload session and store its last interaction time
        user = User.objects.create(username="testuser", password="password")
        upload_session = UploadSession.new_session(user=user)
        initial_interaction_time = upload_session.last_upload_interaction_time

        # Create and save an InProgressSubmission with the upload session
        in_progress_submission = InProgressSubmission(
            upload_session=upload_session,
            user=upload_session.user,
            current_step=TransferStep.UPLOAD_FILES.value,
        )
        in_progress_submission.save()

        # Get the updated upload session from database
        upload_session.refresh_from_db()

        # Verify the last interaction time was updated
        self.assertGreater(
            upload_session.last_upload_interaction_time,
            initial_interaction_time
        )
