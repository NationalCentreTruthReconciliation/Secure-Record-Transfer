# pylint: disable=too-many-public-methods
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, PropertyMock, patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.manager import BaseManager
from django.test import TestCase, override_settings

from recordtransfer.models import UploadedFile, UploadSession


def get_mock_uploaded_file(
    name: str,
    exists: bool = True,
    session: Optional[UploadSession] = None,
    upload_to: str = "/media/",
    size: int = 1024,
) -> MagicMock:
    """Create a new MagicMock that implements all the correct properties
    required for an UploadedFile.
    """
    if not exists:
        size = 0
    file_mock = MagicMock(spec=UploadedFile)
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

    def test_empty_session(self) -> None:
        """Test that a new session has no files."""
        session = UploadSession.new_session()
        session.save()

        self.assertEqual(len(session.get_existing_file_set()), 0)
        self.assertEqual(session.upload_size, 0)

        session.delete()

    @patch("recordtransfer.models.UploadSession.uploadedfile_set", spec=BaseManager)
    def test_one_file_in_session(self, uploadedfile_set_mock: BaseManager) -> None:
        """Test that a session with one file returns correct file count and size."""
        session = UploadSession.new_session()
        session.save()

        uploadedfile_set_mock.all = MagicMock(
            return_value=[
                get_mock_uploaded_file("1.pdf", size=1000),
            ]
        )

        self.assertEqual(len(session.get_existing_file_set()), 1)
        self.assertEqual(session.upload_size, 1000)

        session.delete()

    @patch("recordtransfer.models.UploadSession.uploadedfile_set", spec=BaseManager)
    def test_multiple_files_in_session(self, uploadedfile_set_mock: BaseManager) -> None:
        """Test that a session with multiple files returns correct file count and size."""
        session = UploadSession.new_session()
        session.save()

        uploadedfile_set_mock.all = MagicMock(
            return_value=[
                get_mock_uploaded_file("1.pdf", size=1000),
                get_mock_uploaded_file("2.pdf", size=1000),
                get_mock_uploaded_file("3.pdf", size=1000),
                get_mock_uploaded_file("4.pdf", size=1000),
                get_mock_uploaded_file("5.pdf", size=1000),
            ]
        )

        self.assertEqual(len(session.get_existing_file_set()), 5)
        self.assertEqual(session.upload_size, 5000)

        session.delete()

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

        self.assertEqual(len(session.get_existing_file_set()), 2)
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

        session.remove_session_uploads()

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
        session = UploadSession.new_session()
        session.save()

        file_1 = get_mock_uploaded_file("1.pdf")
        file_2 = get_mock_uploaded_file("2.pdf")
        file_3 = get_mock_uploaded_file("3.pdf", exists=False)

        uploadedfile_set_mock.all = MagicMock(return_value=[file_1, file_2, file_3])

        session.move_uploads_to_permanent_storage()

        file_1.move_to_permanent_storage.assert_called_once()
        file_2.move_to_permanent_storage.assert_called_once()
        file_3.move_to_permanent_storage.assert_not_called()

    @classmethod
    def tearDownClass(cls) -> None:
        """Restore logging settings."""
        super().tearDownClass()
        logging.disable(logging.NOTSET)


class TestUploadedFile(TestCase):
    """Tests for the UploadedFile model."""

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

        self.uploaded_file = UploadedFile(
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
        for file_path in settings.TEMP_STORAGE_FOLDER.rglob("test.pdf"):
            if file_path.exists():
                print("Deleting found file from: ", file_path)
                file_path.unlink()
        self.assertFalse(self.uploaded_file.exists)

    def test_copy(self) -> None:
        """Test that the file is copied."""
        temp_dir = tempfile.mkdtemp()
        self.uploaded_file.copy(temp_dir)
        self.assertTrue(Path(temp_dir, "test.pdf").exists())
        self.assertTrue(self.uploaded_file.exists)

    def test_move(self) -> None:
        """Test that the file is moved."""
        temp_dir = tempfile.mkdtemp()
        self.uploaded_file.move(temp_dir)
        self.assertFalse(self.uploaded_file.exists)
        self.assertTrue(Path(temp_dir, "test.pdf").exists())

    def test_remove(self) -> None:
        """Test that the file is removed."""
        self.uploaded_file.remove()
        self.assertFalse(self.uploaded_file.exists)

    def test_get_temp_file_media_url(self) -> None:
        """Test that the file media URL is returned."""
        self.assertEqual(
            self.uploaded_file.get_file_media_url(),
            settings.MEDIA_URL + settings.TEMP_URL + self.uploaded_file.file_upload.name
        )



    def tearDown(cls) -> None:
        """Tear down test."""
        UploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()

        # Clear everything in the temp and upload storage folders
        shutil.rmtree(settings.TEMP_STORAGE_FOLDER)
        shutil.rmtree(settings.UPLOAD_STORAGE_FOLDER)

        # Recreate the directories
        settings.TEMP_STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)
        settings.UPLOAD_STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        """Restore logging settings."""
        super().tearDownClass()
        logging.disable(logging.NOTSET)
