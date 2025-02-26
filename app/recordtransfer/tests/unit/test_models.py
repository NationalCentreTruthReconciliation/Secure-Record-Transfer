import logging
import shutil
import tempfile
from datetime import datetime, timedelta
from datetime import timezone as dttimezone
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.manager import BaseManager
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from recordtransfer.enums import TransferStep
from recordtransfer.models import (
    InProgressSubmission,
    PermUploadedFile,
    TempUploadedFile,
    UploadSession,
    User,
)


def get_mock_temp_uploaded_file(
    name: str,
    exists: bool = True,
    session: Optional[UploadSession] = None,
    upload_to: str = "/media/temp/",
    size: int = 1024,
) -> MagicMock:
    """Create a new MagicMock that implements all the correct properties
    required for an TempUploadedFile.
    """
    if not exists:
        size = 0
    file_mock = MagicMock(spec_set=TempUploadedFile)
    file_mock.exists = exists
    file_mock.name = name
    file_mock.session = session

    file_upload_mock = MagicMock()
    file_upload_mock.size = size
    file_upload_mock.path = f"{upload_to.rstrip('/')}/{name}"
    file_upload_mock.name = name

    file_mock.file_upload = file_upload_mock

    return file_mock


def get_mock_perm_uploaded_file(
    name: str,
    exists: bool = True,
    session: Optional[UploadSession] = None,
    upload_to: str = "/media/uploaded_files/",
    size: int = 1024,
) -> MagicMock:
    """Create a new MagicMock that implements all the correct properties
    required for an PermUploadedFile.
    """
    if not exists:
        size = 0
    file_mock = MagicMock(spec_set=PermUploadedFile)
    file_mock.exists = exists
    file_mock.name = name
    file_mock.session = session

    file_upload_mock = MagicMock()
    file_upload_mock.size = size
    file_upload_mock.path = f"{upload_to.rstrip('/')}/{name}"
    file_upload_mock.name = name

    file_mock.file_upload = file_upload_mock

    return file_mock


class TestUploadSession(TestCase):
    """Tests for the UploadSession model."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        """Set up test."""
        self.session = UploadSession.new_session()

        self.test_temp_file = get_mock_temp_uploaded_file(
            "test.pdf", size=1000, session=self.session
        )
        self.test_perm_file = get_mock_perm_uploaded_file(
            "test.pdf", size=1000, session=self.session
        )
        self.test_file_1 = SimpleUploadedFile(
            "test1.pdf", b"Test file content", content_type="application/pdf"
        )
        self.test_file_2 = SimpleUploadedFile(
            "test2.pdf", b"Test file content", content_type="application/pdf"
        )

    def test_new_session_creation(self) -> None:
        """Test creating a new upload session."""
        self.assertIsInstance(self.session, UploadSession)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.CREATED)
        self.assertEqual(len(self.session.token), 32)
        self.assertIsNotNone(self.session.last_upload_interaction_time)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_expires_at_valid_states(self) -> None:
        """Test expires_at returns the correct expiration time for sessions in CREATED and
        UPLOADING states.
        """
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        self.session.last_upload_interaction_time = fixed_now
        expected_expires_at = fixed_now + timezone.timedelta(minutes=30)
        valid_states = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
        ]

        for state in valid_states:
            self.session.status = state
            self.assertEqual(self.session.expires_at, expected_expires_at)

    def test_expires_at_invalid_states(self) -> None:
        """Test expires_at raises an exception for sessions in states other than CREATED or
        UPLOADING.
        """
        invalid_states = [
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            UploadSession.SessionStatus.STORED,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for state in invalid_states:
            self.session.status = state
            self.assertIsNone(self.session.expires_at)

    def test_expires_when_expiry_disabled(self) -> None:
        """Test expires_at returns None when the upload session expiry is disabled."""
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        self.session.last_upload_interaction_time = fixed_now
        self.session.status = UploadSession.SessionStatus.UPLOADING
        with patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", -1):
            self.assertIsNone(self.session.expires_at)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.utils.timezone.now")
    def test_expired_is_true(self, mock_now: MagicMock) -> None:
        """Test expired property is True for a session that has expired."""
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timezone.timedelta(minutes=31)

        valid_states = [UploadSession.SessionStatus.CREATED, UploadSession.SessionStatus.UPLOADING]

        for state in valid_states:
            # Test expired returns True for a session that has expired
            self.session.status = state
            self.assertTrue(self.session.expired)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.utils.timezone.now")
    def test_expired_is_false(self, mock_now: MagicMock) -> None:
        """Test expired property is False for a session that has not expired."""
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timezone.timedelta(minutes=29)

        valid_states = [UploadSession.SessionStatus.CREATED, UploadSession.SessionStatus.UPLOADING]

        for state in valid_states:
            # Test expired returns False for a session that has not expired
            self.session.status = state
            self.assertFalse(self.session.expired)

    def test_expired_invalid_states(self) -> None:
        """Test expired property is False for sessions in states other than CREATED or
        UPLOADING.
        """
        # Test expired returns False for sessions in states other than CREATED or UPLOADING
        invalid_states = [
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            UploadSession.SessionStatus.STORED,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for state in invalid_states:
            self.session.status = state
            self.assertFalse(self.session.expired)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", -1)
    @patch("django.utils.timezone.now")
    def test_expired_when_expiry_disabled(self, mock_now: MagicMock) -> None:
        """Test expired property is False when the upload session expiry is disabled."""
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timezone.timedelta(minutes=31)

        self.assertFalse(self.session.expired)

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    def test_expires_within_true(self, mock_now: MagicMock) -> None:
        """Test expires_within returns True when the session will expire within the given
        minutes.
        """
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timedelta(minutes=31)

        self.assertTrue(self.session.expires_within(30))

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    def test_expires_within_false(self, mock_now: MagicMock) -> None:
        """Test expires_within returns False when the session will not expire within the given
        minutes.
        """
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timedelta(minutes=10)

        self.assertFalse(self.session.expires_within(10))

    def test_expires_within_no_expiry_time(self) -> None:
        """Test expires_within returns False when the session is not in a valid state to check
        expiry.
        """
        self.session.status = UploadSession.SessionStatus.STORED
        self.assertFalse(self.session.expires_within(10))

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.utils.timezone.now")
    def test_expires_soon_true(self, mock_now: MagicMock) -> None:
        """Test expires_soon returns True when the session will expire within the reminder time."""
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timedelta(minutes=31)

        self.assertTrue(self.session.expires_soon)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.utils.timezone.now")
    def test_expires_soon_false(self, mock_now: MagicMock) -> None:
        """Test expires_soon returns False when the session will not expire within the reminder
        time.
        """
        fixed_now = datetime(2025, 2, 18, 12, 0, 0)
        mock_now.return_value = fixed_now
        self.session.last_upload_interaction_time = fixed_now - timedelta(minutes=15)

        self.assertFalse(self.session.expires_soon)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", -1)
    def test_expires_soon_disabled(self) -> None:
        """Test expires_soon returns False when the reminder feature is disabled."""
        self.assertFalse(self.session.expires_soon)

    def test_upload_size_created_session(self) -> None:
        """Test upload size should be zero for a newly created session."""
        self.assertEqual(self.session.upload_size, 0)

    @patch("django.utils.timezone.now")
    def test_touch_valid_states(self, mock_now: MagicMock) -> None:
        """Test that touch() updates last_upload_interaction_time with current time."""
        # Setup fixed time
        fixed_now = timezone.datetime(2025, 2, 18, 12, 0, 0, tzinfo=dttimezone.utc)
        mock_now.return_value = fixed_now

        valid_states = [UploadSession.SessionStatus.CREATED, UploadSession.SessionStatus.UPLOADING]

        for state in valid_states:
            self.session.status = state
            self.session.touch()
            self.assertEqual(self.session.last_upload_interaction_time, fixed_now)

    def test_touch_invalid_states(self) -> None:
        """Test that touch() does nothing when session is in invalid state."""
        original_time = self.session.last_upload_interaction_time

        invalid_states = [
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            UploadSession.SessionStatus.STORED,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]

        for state in invalid_states:
            self.session.status = state
            self.session.touch()
            self.assertEqual(self.session.last_upload_interaction_time, original_time)

    @patch("django.utils.timezone.now")
    def test_touch_with_save_flag_false(self, mock_now: MagicMock) -> None:
        """Test that touch() respects the save flag when save=False."""
        fixed_now = timezone.datetime(2025, 2, 18, 12, 0, 0, tzinfo=dttimezone.utc)
        mock_now.return_value = fixed_now

        # Test with save=False
        self.session.status = UploadSession.SessionStatus.UPLOADING
        self.session.touch(save=False)

        # Refresh from db to verify it wasn't saved
        original_session = UploadSession.objects.get(pk=self.session.pk)
        self.assertNotEqual(original_session.last_upload_interaction_time, fixed_now)

    @patch("django.utils.timezone.now")
    def test_touch_with_save_flag_true(self, mock_now: MagicMock) -> None:
        """Test that touch() respects the save flag when save=True."""
        fixed_now = timezone.datetime(2025, 2, 18, 12, 0, 0, tzinfo=dttimezone.utc)
        mock_now.return_value = fixed_now

        # Test with save=True
        self.session.status = UploadSession.SessionStatus.UPLOADING
        self.session.touch(save=True)

        # Refresh from db to verify it was saved
        original_session = UploadSession.objects.get(pk=self.session.pk)
        self.assertEqual(original_session.last_upload_interaction_time, fixed_now)

    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set", spec=BaseManager)
    def test_upload_size_one_file(self, tempuploadedfile_set_mock: BaseManager) -> None:
        """Test upload size should be the size of the uploaded file."""
        tempuploadedfile_set_mock.all = MagicMock(
            return_value=[
                self.test_temp_file,
            ]
        )
        self.session.status = UploadSession.SessionStatus.UPLOADING
        self.assertEqual(self.session.upload_size, 1000)

    def test_upload_size_raises_for_invalid_status(self) -> None:
        """Test upload_size raises ValueError when session is expired or deleted."""
        statuses = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                _ = self.session.upload_size

    def test_file_count_created_session(self) -> None:
        """Test file count should be zero for a newly created session."""
        self.assertEqual(self.session.file_count, 0)

    @patch("recordtransfer.models.UploadSession.permuploadedfile_set", spec=BaseManager)
    def test_file_count_one_file(self, permuploadedfile_set_mock: BaseManager) -> None:
        """Test file count should be one for a session with one file."""
        permuploadedfile_set_mock.all = MagicMock(
            return_value=[
                self.test_perm_file,
            ]
        )
        self.session.status = UploadSession.SessionStatus.UPLOADING
        self.assertEqual(self.session.file_count, 1)

    def test_file_count_raises_for_invalid_status(self) -> None:
        """Test file_count raises ValueError when session is in an invalid state for checking
        file count.
        """
        statuses = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                _ = self.session.file_count

    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set", spec=BaseManager)
    @patch("recordtransfer.models.UploadSession.permuploadedfile_set", spec=BaseManager)
    def test_multiple_files_in_session(
        self, tempuploadedfile_set_mock: BaseManager, permuploadedfile_set_mock: BaseManager
    ) -> None:
        """Test that a session with multiple files returns correct file count and size."""
        tempuploadedfile_set_mock.all = MagicMock(
            return_value=[
                self.test_temp_file,
            ]
        )
        permuploadedfile_set_mock.all = MagicMock(
            return_value=[
                self.test_perm_file,
            ]
        )
        self.session.status = UploadSession.SessionStatus.UPLOADING

        self.assertEqual(self.session.file_count, 2)
        self.assertEqual(self.session.upload_size, 2000)

    def test_add_temp_file(self) -> None:
        """Test adding a temp file to the session."""
        self.assertEqual(len(self.session.tempuploadedfile_set.all()), 0)
        temp_file = self.session.add_temp_file(self.test_file_1)

        self.assertEqual(len(self.session.tempuploadedfile_set.all()), 1)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.UPLOADING)

        self.assertEqual(temp_file.name, self.test_file_1.name)
        self.assertEqual(temp_file.session, self.session)
        self.assertTrue(temp_file.exists)

    def test_add_temp_file_invalid_status(self) -> None:
        """Test adding a temp file to the session raises an exception when the session is in an
        invalid state.
        """
        statuses = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            UploadSession.SessionStatus.STORED,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.add_temp_file(self.test_file_1)

    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set", spec=BaseManager)
    def test_remove_temp_file_by_name(self, mock_temp_files: BaseManager) -> None:
        """Test removing temp files from the session by name."""
        # Setup
        test_temp_file_1 = get_mock_temp_uploaded_file(
            "test1.pdf", size=1000, session=self.session
        )
        test_temp_file_2 = get_mock_temp_uploaded_file(
            "test2.pdf", size=1000, session=self.session
        )
        mock_temp_files.all = MagicMock(
            return_value=[
                test_temp_file_1,
                test_temp_file_2,
            ]
        )
        temp_file_dict = {"test1.pdf": test_temp_file_1, "test2.pdf": test_temp_file_2}
        mock_temp_files.get = MagicMock(side_effect=lambda name: temp_file_dict[name])

        self.session.status = UploadSession.SessionStatus.UPLOADING

        def delete_first_file_side_effect():
            # Modify mock to reflect the removal
            mock_temp_files.all = MagicMock(return_value=[test_temp_file_2])
            temp_file_dict.pop(test_temp_file_1.name)

        test_temp_file_1.delete.side_effect = delete_first_file_side_effect
        # Remove first file
        self.session.remove_temp_file_by_name(test_temp_file_1.name)
        test_temp_file_1.delete.assert_called_once()
        self.assertEqual(self.session.status, UploadSession.SessionStatus.UPLOADING)

        def delete_second_file_side_effect():
            # Modify mock to reflect the removal
            mock_temp_files.all = MagicMock(return_value=[])
            temp_file_dict.pop(test_temp_file_2.name)

        test_temp_file_2.delete.side_effect = delete_second_file_side_effect
        # Remove second file
        self.session.remove_temp_file_by_name(test_temp_file_2.name)
        test_temp_file_2.delete.assert_called_once()
        self.assertEqual(self.session.status, UploadSession.SessionStatus.CREATED)

    def test_remove_temp_file_by_name_invalid_status(self) -> None:
        """Test removing temp files from the session by name raises an exception when the session
        is in an invalid state.
        """
        statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            UploadSession.SessionStatus.STORED,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.remove_temp_file_by_name(self.test_file_1.name)

    def test_remove_temp_file_by_name_file_not_found(self) -> None:
        """Test removing temp files from the session by name raises an exception when the file is
        not found.
        """
        self.session.status = UploadSession.SessionStatus.UPLOADING
        with self.assertRaises(FileNotFoundError):
            self.session.remove_temp_file_by_name("non_existent_file.pdf")

    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set", spec=BaseManager)
    def test_get_temp_file_by_name(self, mock_temp_files: BaseManager) -> None:
        """Test getting a temp file from the session by name."""
        mock_temp_files.get = MagicMock(return_value=self.test_temp_file)
        self.session.status = UploadSession.SessionStatus.UPLOADING
        temp_uploaded_file = self.session.get_temp_file_by_name(self.test_temp_file.name)
        self.assertIsNotNone(temp_uploaded_file)
        self.assertEqual(temp_uploaded_file.name, self.test_temp_file.name)

    def test_get_temp_file_by_name_invalid_status(self) -> None:
        """Test getting a temp file from the session by name raises an exception when the session
        is in an invalid state.
        """
        self.session.add_temp_file(self.test_file_1)
        statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            UploadSession.SessionStatus.STORED,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.get_temp_file_by_name(self.test_file_1.name)

    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set", spec=BaseManager)
    def test_get_temporary_uploads(self, mock_temp_files: BaseManager) -> None:
        """Test getting temporary uploads."""
        test_temp_file_1 = get_mock_temp_uploaded_file(
            "test1.pdf", size=1000, session=self.session
        )
        test_temp_file_2 = get_mock_temp_uploaded_file(
            "test2.pdf", size=1000, session=self.session
        )
        mock_temp_files.all = MagicMock(
            return_value=[
                test_temp_file_1,
                test_temp_file_2,
            ]
        )
        self.session.status = UploadSession.SessionStatus.UPLOADING

        temp_uploads = self.session.get_temporary_uploads()
        self.assertEqual(len(temp_uploads), 2)
        self.assertIn(self.test_file_1.name, [file.name for file in temp_uploads])
        self.assertIn(self.test_file_2.name, [file.name for file in temp_uploads])

    def test_get_temporary_uploads_empty(self) -> None:
        """Test getting temporary uploads when the session is newly created or if all temporary
        files have been moved to permanent storage.
        """
        temp_uploads = self.session.get_temporary_uploads()
        self.assertEqual(len(temp_uploads), 0)
        self.session.status = UploadSession.SessionStatus.STORED
        temp_uploads = self.session.get_temporary_uploads()
        self.assertEqual(len(temp_uploads), 0)

    def test_get_temporary_uploads_invalid_status(self) -> None:
        """Test getting temporary uploads raises an exception when the session is in an invalid
        state.
        """
        statuses = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            # UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                _ = self.session.get_temporary_uploads()

    @patch("recordtransfer.models.UploadSession.permuploadedfile_set", spec=BaseManager)
    def test_get_permanent_uploads(self, permuploadedfile_set_mock: BaseManager) -> None:
        """Test getting permanent uploads."""
        permuploadedfile_set_mock.all = MagicMock(
            return_value=[
                self.test_perm_file,
            ]
        )
        self.session.status = UploadSession.SessionStatus.STORED
        perm_uploads = self.session.get_permanent_uploads()
        self.assertEqual(len(perm_uploads), 1)

    def test_get_permanent_uploads_empty(self) -> None:
        """Test getting permanent uploads when the session is newly created or if uploaded files
        are still temporary.
        """
        perm_uploads = self.session.get_permanent_uploads()
        self.assertEqual(len(perm_uploads), 0)
        self.session.status = UploadSession.SessionStatus.UPLOADING
        perm_uploads = self.session.get_permanent_uploads()
        self.assertEqual(len(perm_uploads), 0)

    def test_get_permanent_uploads_invalid_status(self) -> None:
        """Test getting permanent uploads raises an exception when the session is in an invalid
        state.
        """
        statuses = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
            # UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for status in statuses:
            self.session.status = status
            with self.assertRaises(ValueError):
                _ = self.session.get_permanent_uploads()

    @patch("recordtransfer.models.UploadSession.get_temporary_uploads")
    @patch("recordtransfer.models.UploadSession.get_permanent_uploads")
    def test_get_uploads(
        self, mock_get_permanent: MagicMock, mock_get_temporary: MagicMock
    ) -> None:
        """Test getting uploads returns correct files based on session status."""
        # Setup mock returns
        temp_files = [self.test_temp_file]
        perm_files = [self.test_perm_file]
        mock_get_temporary.return_value = temp_files
        mock_get_permanent.return_value = perm_files

        # Test UPLOADING state
        self.session.status = UploadSession.SessionStatus.UPLOADING
        result = self.session.get_uploads()
        self.assertEqual(result, temp_files)
        mock_get_temporary.assert_called_once()
        mock_get_permanent.assert_not_called()

        # Reset mocks
        mock_get_temporary.reset_mock()
        mock_get_permanent.reset_mock()

        # Test STORED state
        self.session.status = UploadSession.SessionStatus.STORED
        result = self.session.get_uploads()
        self.assertEqual(result, perm_files)
        mock_get_permanent.assert_called_once()
        mock_get_temporary.assert_not_called()

        # Test invalid states
        invalid_states = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
        ]

        for status in invalid_states:
            mock_get_temporary.reset_mock()
            mock_get_permanent.reset_mock()
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.get_uploads()
            mock_get_temporary.assert_not_called()
            mock_get_permanent.assert_not_called()

    @patch("recordtransfer.models.UploadSession.permuploadedfile_set")
    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set")
    def test_remove_uploads(
        self, mock_temp_files: BaseManager, mock_perm_files: BaseManager
    ) -> None:
        """Test the remove_uploads method of UploadSession."""
        # Setup mock files
        mock_file1 = Mock()
        mock_file2 = Mock()
        mock_temp_files.all = MagicMock(return_value=[mock_file1])
        mock_perm_files.all = MagicMock(return_value=[mock_file2])

        # Valid statuses for upload removal
        valid_statuses = [
            UploadSession.SessionStatus.UPLOADING,
            UploadSession.SessionStatus.STORED,
        ]

        # Test successful removal
        for status in valid_statuses:
            self.session.status = status
            self.session.remove_uploads()

            mock_file1.remove.assert_called_once()
            mock_file2.remove.assert_called_once()
            self.assertEqual(self.session.status, UploadSession.SessionStatus.DELETED)

            # Reset mock files
            mock_file1.reset_mock()
            mock_file2.reset_mock()

        valid_unchanged_statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
        ]
        for status in valid_unchanged_statuses:
            self.session.status = status
            self.session.remove_uploads()
            mock_file1.remove.assert_not_called()
            mock_file2.remove.assert_not_called()
            self.assertEqual(self.session.status, status)

        # Test invalid states
        invalid_states = [
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
        ]
        for status in invalid_states:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.remove_uploads()

    @patch("recordtransfer.models.UploadSession.tempuploadedfile_set", spec=BaseManager)
    def test_make_uploads_permanent(self, tempuploadedfile_set_mock: BaseManager) -> None:
        """Test making temporary uploaded files permanent in different session states."""
        # Create mock uploaded files
        mock_file = get_mock_temp_uploaded_file("1.pdf", session=self.session)
        tempuploadedfile_set_mock.all = MagicMock(return_value=[mock_file])

        # Test already stored state - should not attempt to move files
        self.session.status = UploadSession.SessionStatus.STORED
        self.session.make_uploads_permanent()
        mock_file.move_to_permanent_storage.assert_not_called()

        mock_file.reset_mock()

        # Test successful move to permanent storage
        self.session.status = UploadSession.SessionStatus.UPLOADING
        self.session.make_uploads_permanent()
        mock_file.move_to_permanent_storage.assert_called_once()
        self.assertEqual(self.session.status, UploadSession.SessionStatus.STORED)

        mock_file.reset_mock()

        # Test error during move
        mock_file.move_to_permanent_storage.side_effect = Exception("Test error")
        self.session.status = UploadSession.SessionStatus.UPLOADING
        self.session.make_uploads_permanent()
        mock_file.move_to_permanent_storage.assert_called_once()
        self.assertEqual(self.session.status, UploadSession.SessionStatus.COPYING_FAILED)

        # Test invalid states
        invalid_states = [
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.COPYING_FAILED,
        ]
        for status in invalid_states:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.make_uploads_permanent()

    @patch("recordtransfer.models.UploadSession.permuploadedfile_set", spec=BaseManager)
    def test_copy_session_uploads(self, permuploadedfile_set_mock: BaseManager) -> None:
        """Test copying session uploads to destination."""
        # Setup
        dest_path = tempfile.mkdtemp()
        permuploadedfile_set_mock.all = MagicMock(
            return_value=[
                self.test_perm_file,
            ]
        )
        self.session.status = UploadSession.SessionStatus.STORED

        # Test successful copy
        copied, missing = self.session.copy_session_uploads(str(dest_path))
        self.assertEqual(len(copied), 1)
        self.assertEqual(len(missing), 0)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.STORED)

        # Test copying a file that does not exist
        self.test_perm_file.exists = False
        copied, missing = self.session.copy_session_uploads(str(dest_path))
        self.assertEqual(len(copied), 0)
        self.assertEqual(len(missing), 1)

        # Reset exists property
        self.test_perm_file.exists = True

        # Test copying a file that is missing its name
        self.test_perm_file.name = None
        copied, missing = self.session.copy_session_uploads(str(dest_path))
        self.assertEqual(len(copied), 0)
        self.assertEqual(len(missing), 1)

        # Test invalid session states
        invalid_states = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
        ]
        for status in invalid_states:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.copy_session_uploads(str(dest_path))

        # Test non-existent destination
        self.session.status = UploadSession.SessionStatus.STORED
        with self.assertRaises(FileNotFoundError):
            self.session.copy_session_uploads("/nonexistent/path")

    def tearDown(self) -> None:
        """Tear down test."""
        TempUploadedFile.objects.all().delete()
        PermUploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()

        # Clear everything in the temp and upload storage folders
        shutil.rmtree(Path(settings.TEMP_STORAGE_FOLDER))
        shutil.rmtree(Path(settings.UPLOAD_STORAGE_FOLDER))

        # Recreate the directories
        Path(settings.TEMP_STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(settings.UPLOAD_STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)

    @patch("recordtransfer.models.UploadSession.get_uploads")
    @patch("recordtransfer.models.get_human_readable_file_count")
    @patch("recordtransfer.models.get_human_readable_size")
    def test_get_quantity_and_unit_of_measure(
        self,
        mock_get_human_readable_size: MagicMock,
        mock_get_human_readable_file_count: MagicMock,
        mock_get_uploads: MagicMock,
    ) -> None:
        """Test the get_quantity_and_unit_of_measure method of UploadSession."""
        # Setup mock returns
        mock_get_uploads.return_value = []
        mock_get_human_readable_size.return_value = "0 KB"
        mock_get_human_readable_file_count.return_value = "No files"

        # Test CREATED state
        self.session.status = UploadSession.SessionStatus.CREATED
        result = self.session.get_quantity_and_unit_of_measure()
        self.assertEqual(result, "No files, totalling 0 KB")

        # Setup mock returns
        mock_get_uploads.return_value = [self.test_temp_file]
        mock_get_human_readable_size.return_value = "1 KB"
        mock_get_human_readable_file_count.return_value = "1 file"

        # Test UPLOADING state
        self.session.status = UploadSession.SessionStatus.UPLOADING
        result = self.session.get_quantity_and_unit_of_measure()
        self.assertEqual(result, "1 file, totalling 1 KB")

        # Test STORED state
        self.session.status = UploadSession.SessionStatus.STORED
        result = self.session.get_quantity_and_unit_of_measure()
        self.assertEqual(result, "1 file, totalling 1 KB")

        # Test invalid states
        invalid_states = [
            UploadSession.SessionStatus.DELETED,
            UploadSession.SessionStatus.EXPIRED,
            UploadSession.SessionStatus.COPYING_IN_PROGRESS,
            UploadSession.SessionStatus.REMOVING_IN_PROGRESS,
        ]
        for status in invalid_states:
            self.session.status = status
            with self.assertRaises(ValueError):
                self.session.get_quantity_and_unit_of_measure()

    @classmethod
    def tearDownClass(cls) -> None:
        """Restore logging settings."""
        super().tearDownClass()
        logging.disable(logging.NOTSET)


class TestPermUploadedFile(TestCase):
    """Test the PermUploadedFile model."""

    model_class = PermUploadedFile

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        """Set up test."""
        self.session = UploadSession.new_session()

        test_file_content = b"Test file content"
        test_file = SimpleUploadedFile(
            "test.pdf", test_file_content, content_type="application/pdf"
        )

        self.uploaded_file = self.model_class.objects.create(
            name="test.pdf",
            session=self.session,
            file_upload=test_file,
        )
        self.uploaded_file.save()

    def test_file_exists(self) -> None:
        """Test that the file exists."""
        self.assertTrue(self.uploaded_file.exists)

    def test_file_does_not_exist(self) -> None:
        """Test that the file does not exist."""
        # Delete the uploaded file from the file system
        self.uploaded_file.file_upload.delete()
        self.assertFalse(self.uploaded_file.exists)

    def test_copy(self) -> None:
        """Test that the file is copied."""
        temp_dir = tempfile.mkdtemp()
        self.uploaded_file.copy(temp_dir)
        self.assertTrue(Path(temp_dir, "test.pdf").exists())
        self.assertTrue(
            self.uploaded_file.file_upload.storage.exists(self.uploaded_file.file_upload.name)
        )

    def test_remove(self) -> None:
        """Test that the file is removed."""
        self.uploaded_file.remove()
        self.assertFalse(self.uploaded_file.exists)

    def test_get_file_media_url(self) -> None:
        """Test that the file media URL is returned."""
        if self.model_class == TempUploadedFile:
            self.assertEqual(
                self.uploaded_file.get_file_media_url(),
                "/"
                + (
                    Path(settings.TEMP_STORAGE_FOLDER).relative_to(settings.BASE_DIR)
                    / self.uploaded_file.file_upload.name
                ).as_posix(),
            )
        elif self.model_class == PermUploadedFile:
            self.assertEqual(
                self.uploaded_file.get_file_media_url(),
                "/"
                + (
                    Path(settings.UPLOAD_STORAGE_FOLDER).relative_to(settings.BASE_DIR)
                    / self.uploaded_file.file_upload.name
                ).as_posix(),
            )

    def test_get_file_media_url_no_file(self) -> None:
        """Test that an exception is raised when trying to get the media URL of a non-existent
        file.
        """
        self.uploaded_file.remove()
        self.assertRaises(FileNotFoundError, self.uploaded_file.get_file_media_url)

    def tearDown(self) -> None:
        """Tear down test."""
        TempUploadedFile.objects.all().delete()
        PermUploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()

        # Clear everything in the temp and upload storage folders
        shutil.rmtree(Path(settings.TEMP_STORAGE_FOLDER))
        shutil.rmtree(Path(settings.UPLOAD_STORAGE_FOLDER))

        # Recreate the directories
        Path(settings.TEMP_STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(settings.UPLOAD_STORAGE_FOLDER).mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        """Restore logging settings."""
        super().tearDownClass()
        logging.disable(logging.NOTSET)


class TestTempUploadedFile(TestPermUploadedFile):
    """Tests for the TempUploadedFile model.

    These tests are basically the same as the permanent file tests.
    """

    model_class = TempUploadedFile

    def test_move_to_permanent_storage(self) -> None:
        """Test that the file is moved to permanent storage."""
        relative_path = self.uploaded_file.file_upload.name
        self.uploaded_file.move_to_permanent_storage()
        self.assertTrue(Path(settings.UPLOAD_STORAGE_FOLDER, relative_path).exists())
        self.assertFalse(self.uploaded_file.exists)
        perm_uploaded_file = PermUploadedFile.objects.get(session=self.session, name="test.pdf")
        self.assertTrue(perm_uploaded_file.exists)


class TestInProgressSubmission(TestCase):
    """Tests for the InProgressSubmission model."""

    def setUp(self) -> None:
        """Set up test."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session()
        self.submission = InProgressSubmission.objects.create(
            user=self.user,
            current_step=TransferStep.ACCEPT_LEGAL.value,
            step_data=b"test data",
            title="Test Submission",
            upload_session=self.upload_session,
        )

    def test_clean_invalid_step(self) -> None:
        """Test clean method with an invalid step."""
        self.submission.current_step = "INVALID_STEP"
        with self.assertRaises(ValidationError):
            self.submission.clean()

    def test_upload_session_expires_at(self) -> None:
        """Test upload_session_expires_at method."""
        self.assertEqual(self.submission.upload_session_expires_at, self.upload_session.expires_at)

    def test_upload_session_expires_at_no_session(self) -> None:
        """Test upload_session_expires_at method when there is no upload session."""
        self.submission.upload_session = None
        self.assertIsNone(self.submission.upload_session_expires_at)

    @patch("recordtransfer.models.UploadSession.expired", new_callable=PropertyMock)
    def test_upload_session_expired(self, mock_expired: PropertyMock) -> None:
        """Test upload_session_expired property."""
        mock_expired.return_value = True
        self.assertTrue(self.submission.upload_session_expired)

        mock_expired.return_value = False
        self.assertFalse(self.submission.upload_session_expired)

        self.submission.upload_session = None
        self.assertFalse(self.submission.upload_session_expired)

    @patch("recordtransfer.models.UploadSession.expires_soon", new_callable=PropertyMock)
    def test_upload_session_expires_soon(self, mock_expires_soon: PropertyMock) -> None:
        """Test upload_session_expires_soon property."""
        mock_expires_soon.return_value = True
        self.assertTrue(self.submission.upload_session_expires_soon)

        mock_expires_soon.return_value = False
        self.assertFalse(self.submission.upload_session_expires_soon)

        self.submission.upload_session = None
        self.assertFalse(self.submission.upload_session_expires_soon)

    def test_get_resume_url(self) -> None:
        """Test the get_resume_url method."""
        expected_url = reverse(
            "recordtransfer:transfer", kwargs={"transfer_uuid": self.submission.uuid}
        )
        self.assertEqual(self.submission.get_resume_url(), expected_url)

    def test_reset_reminder_email_sent_flag_true(self) -> None:
        """Test reset_reminder_email_sent method when the flag is True."""
        self.submission.reminder_email_sent = True
        self.submission.reset_reminder_email_sent()
        self.assertFalse(self.submission.reminder_email_sent)

    def test_reset_reminder_email_sent_flag_false(self) -> None:
        """Test reset_reminder_email_sent method when the flag is already False."""
        self.submission.reminder_email_sent = False
        self.submission.reset_reminder_email_sent()
        self.assertFalse(self.submission.reminder_email_sent)

    def test_str(self) -> None:
        """Test the string representation of the InProgressSubmission."""
        session_token = (
            self.submission.upload_session.token if self.submission.upload_session else "None"
        )
        expected_str = (
            f"In-Progress Submission by {self.user} "
            f"(Title: {self.submission.title} | Session: {session_token})"
        )
        self.assertEqual(str(self.submission), expected_str)
