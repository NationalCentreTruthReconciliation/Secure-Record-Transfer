# pylint: disable=too-many-public-methods
import logging
import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, PropertyMock, patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.manager import BaseManager
from django.test import TestCase

from recordtransfer.models import PermUploadedFile, TempUploadedFile, UploadSession


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
    file_mock = MagicMock(spec=TempUploadedFile)
    path = upload_to.rstrip("/") + "/" + name
    type(file_mock).exists = PropertyMock(return_value=exists)
    type(file_mock).name = PropertyMock(return_value=name)
    type(file_mock).session = PropertyMock(return_value=session)
    type(file_mock.file_upload).size = PropertyMock(return_value=size)
    type(file_mock.file_upload).path = PropertyMock(return_value=path)
    type(file_mock.file_upload).name = PropertyMock(return_value=name)
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
    file_mock = MagicMock(spec=PermUploadedFile)
    path = upload_to.rstrip("/") + "/" + name
    type(file_mock).exists = PropertyMock(return_value=exists)
    type(file_mock).name = PropertyMock(return_value=name)
    type(file_mock).session = PropertyMock(return_value=session)
    type(file_mock.file_upload).size = PropertyMock(return_value=size)
    type(file_mock.file_upload).path = PropertyMock(return_value=path)
    type(file_mock.file_upload).name = PropertyMock(return_value=name)
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
        self.session.save()

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

    def test_upload_size_created_session(self) -> None:
        """Test upload size should be zero for a newly created session."""
        self.assertEqual(self.session.upload_size, 0)

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
        self.session.add_temp_file(self.test_file_1)
        self.assertEqual(len(self.session.tempuploadedfile_set.all()), 1)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.UPLOADING)

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

    def test_remove_temp_file_by_name(self) -> None:
        """Test removing temp files from the session by name."""
        self.session.add_temp_file(self.test_file_1)
        self.session.add_temp_file(self.test_file_2)
        self.session.remove_temp_file_by_name(self.test_file_1.name)
        self.assertEqual(len(self.session.tempuploadedfile_set.all()), 1)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.UPLOADING)
        self.session.remove_temp_file_by_name(self.test_file_2.name)
        self.assertEqual(len(self.session.tempuploadedfile_set.all()), 0)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.CREATED)

    def test_remove_temp_file_by_name_invalid_status(self) -> None:
        """Test removing temp files from the session by name raises an exception when the session
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
                self.session.remove_temp_file_by_name(self.test_file_1.name)

    def test_remove_temp_file_by_name_file_not_found(self) -> None:
        """Test removing temp files from the session by name raises an exception when the file is
        not found.
        """
        self.session.add_temp_file(self.test_file_1)
        with self.assertRaises(FileNotFoundError):
            self.session.remove_temp_file_by_name("non_existent_file.pdf")

    def test_get_temp_file_by_name(self) -> None:
        """Test getting a temp file from the session by name."""
        self.session.add_temp_file(self.test_file_1)
        temp_uploaded_file = self.session.get_temp_file_by_name(self.test_file_1.name)
        self.assertIsNotNone(temp_uploaded_file)
        self.assertEqual(temp_uploaded_file.name, self.test_file_1.name)
        self.assertEqual(self.session.status, UploadSession.SessionStatus.UPLOADING)

    def test_get_temp_file_by_name_new_session(self) -> None:
        """Test getting a temp file from a new session by name."""
        self.assertIsNone(self.session.get_temp_file_by_name("test.pdf"))

    def test_get_temp_file_by_name_invalid_status(self) -> None:
        """Test getting a temp file from the session by name raises an exception when the session
        is in an invalid state.
        """
        self.session.add_temp_file(self.test_file_1)
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
                self.session.get_temp_file_by_name(self.test_file_1.name)

    def test_get_temporary_uploads(self) -> None:
        """Test getting temporary uploads."""
        self.session.add_temp_file(self.test_file_1)
        self.session.add_temp_file(self.test_file_2)
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

    @patch("recordtransfer.models.UploadSession.uploadedfile_set", spec=BaseManager)
    def test_some_files_do_not_exist_in_session(self, uploadedfile_set_mock: BaseManager) -> None:
        """Test that a session with some files that do not exist returns correct file count and
        size.
        """
        session = UploadSession.new_session()
        session.save()

        uploadedfile_set_mock.all = MagicMock(
            return_value=[
                get_mock_uploaded_file("1.pdf", size=1000),
                get_mock_uploaded_file("2.pdf", size=1000),
                get_mock_uploaded_file("3.pdf", exists=False),
                get_mock_uploaded_file("4.pdf", exists=False),
            ]
        )

        self.assertEqual(len(session.get_uploaded_files()), 2)
        self.assertEqual(session.upload_size, 2000)

        session.delete()

    @patch("recordtransfer.models.UploadSession.uploadedfile_set", spec=BaseManager)
    def test_delete_files_in_session(self, uploadedfile_set_mock: BaseManager) -> None:
        """Test that a session with files that exist are removed when delete is called
        on the session.
        """
        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file("1.pdf")
        file_2 = get_mock_uploaded_file("2.pdf")
        file_3 = get_mock_uploaded_file("3.pdf", exists=False)

        uploadedfile_set_mock.all = MagicMock(return_value=[file_1, file_2, file_3])

        session._remove_temp_uploads()

        file_1.remove.assert_called_once()
        file_2.remove.assert_called_once()
        file_3.remove.assert_not_called()

        session.delete()

    @patch("recordtransfer.models.UploadSession.uploadedfile_set", spec=BaseManager)
    def test_copy_files_in_session(self, uploadedfile_set_mock: BaseManager) -> None:
        """Test that a session with files that exist are copied when copy is called."""
        mock_path_exists = patch.object(Path, "exists").start()
        mock_path_exists.return_value = True

        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file("1.pdf")
        file_2 = get_mock_uploaded_file("2.pdf")
        file_3 = get_mock_uploaded_file("3.pdf", exists=False)

        uploadedfile_set_mock.all = MagicMock(return_value=[file_1, file_2, file_3])

        copied, missing = session.copy_session_uploads("/home/")

        file_1.copy.assert_called_once_with(Path("/home/1.pdf"))
        file_2.copy.assert_called_once_with(Path("/home/2.pdf"))
        file_3.copy.assert_not_called()
        self.assertIn(str(Path("/home/1.pdf")), copied)
        self.assertIn(str(Path("/home/2.pdf")), copied)
        self.assertEqual(len(missing), 1)

        session.delete()
        mock_path_exists.stop()

    @patch("recordtransfer.models.UploadSession.uploadedfile_set", spec=BaseManager)
    def test_move_file_to_permanent_storage(self, uploadedfile_set_mock: BaseManager) -> None:
        """Test that files are moved to permanent storage."""
        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file("1.pdf")
        file_2 = get_mock_uploaded_file("2.pdf")
        file_3 = get_mock_uploaded_file("3.pdf", exists=False)

        uploadedfile_set_mock.all = MagicMock(return_value=[file_1, file_2, file_3])

        session.move_temp_uploads_to_permanent_storage()

        file_1.move_to_permanent_storage.assert_called_once()
        file_2.move_to_permanent_storage.assert_called_once()
        file_3.move_to_permanent_storage.assert_not_called()

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


class TestBaseUploadedFile(TestCase, ABC):
    """Tests for the BaseUploadedFile model."""

    @property
    @abstractmethod
    def model_class(self) -> type:
        """Must be implemented by child classes."""
        pass

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        """Set up test."""
        self.session = UploadSession.new_session()
        self.session.save()

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


class TestTempUploadedFile(TestBaseUploadedFile):
    """Tests for the TempUploadedFile model."""

    @property
    def model_class(self) -> type:
        """Return the TempUploadedFile model class."""
        return TempUploadedFile

    def test_move_to_permanent_storage(self) -> None:
        """Test that the file is moved to permanent storage."""
        relative_path = self.uploaded_file.file_upload.name
        self.uploaded_file.move_to_permanent_storage()
        self.assertTrue(Path(settings.UPLOAD_STORAGE_FOLDER, relative_path).exists())
        self.assertFalse(self.uploaded_file.exists)
        perm_uploaded_file = PermUploadedFile.objects.get(session=self.session, name="test.pdf")
        self.assertTrue(perm_uploaded_file.exists)


class TestPermUploadedFile(TestBaseUploadedFile):
    """Tests for the PermUploadedFile model."""

    @property
    def model_class(self) -> type:
        """Return the PermUploadedFile model class."""
        return PermUploadedFile
