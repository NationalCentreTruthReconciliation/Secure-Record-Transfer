import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest.mock import MagicMock, PropertyMock, patch

import bagit
from caais.models import Metadata
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from upload.models import PermUploadedFile, TempUploadedFile, UploadSession

from recordtransfer.enums import SiteSettingType, SubmissionStep
from recordtransfer.models import (
    InProgressSubmission,
    Job,
    SiteSetting,
    Submission,
    User,
)


def get_mock_temp_uploaded_file(
    name: str,
    exists: bool = True,
    session: UploadSession | None = None,
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


class TestSubmission(TestCase):
    """Tests for the Submission model."""

    HELLO_FILE_MD5 = "5a8dd3ad0756a93ded72b823b19dd877"
    WORLD_FILE_MD5 = "08cf82251c975a5e9734699fadf5e9c0"

    def setUp(self) -> None:
        """Set up test."""
        self.user = User.objects.create(username="testuser", password="password")

        self.upload_session = UploadSession.new_session()
        self.upload_session.status = UploadSession.SessionStatus.STORED
        self.upload_session.save()

        self.test_perm_file_unexpected_1 = get_mock_perm_uploaded_file(
            "test.pdf", size=1024, session=self.upload_session
        )

        self.test_perm_file_unexpected_2 = get_mock_perm_uploaded_file(
            "README.md", size=512, session=self.upload_session
        )

        self.test_perm_file_expected_1 = get_mock_perm_uploaded_file(
            "hello.txt", size=7, session=self.upload_session
        )

        self.test_perm_file_expected_2 = get_mock_perm_uploaded_file(
            "world.txt", size=7, session=self.upload_session
        )

        self.metadata = Metadata.objects.create(accession_title="My Test Title")

        self.submission = Submission(
            user=self.user,
            metadata=self.metadata,
            uuid="2a7262f5-07a4-49a3-a351-dc1269d7822b",
            upload_session=self.upload_session,
        )

    def tearDown(self) -> None:
        """Remove any temp files created during test."""
        for item in Path(settings.TEMP_STORAGE_FOLDER).iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

    def _create_new_files_OK(self, loc: str) -> tuple[list[str], list[str]]:
        """Create hello.txt and world.txt."""
        with open(Path(loc) / "hello.txt", "w") as fp:
            fp.write("hello!")
        with open(Path(loc) / "world.txt", "w") as fp:
            fp.write("world!")
        return (["hello.txt", "world.txt"], [])

    def _create_new_files_MISSING(self, loc: str) -> tuple[list[str], list[str]]:
        """Create hello.txt, but world.txt is missing."""
        with open(Path(loc) / "hello.txt", "w") as fp:
            fp.write("hello!")
        return (["hello.txt"], ["world.txt"])

    def test_create_bag_exception_if_no_metadata(self) -> None:
        """Assert that a ValueError is raised if there's no Metadata."""
        self.improper_submission = Submission(
            user=self.user,
            upload_session=self.upload_session,
        )

        with (
            self.assertRaises(ValueError),
            TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir,
        ):
            self.improper_submission.make_bag(Path(temp_dir), ["md5"])

    def test_create_bag_exception_if_no_upload(self) -> None:
        """Assert that a ValueError is raised if there's no UploadSession."""
        self.improper_submission = Submission(
            user=self.user,
            metadata=self.metadata,
        )

        with (
            self.assertRaises(ValueError),
            TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir,
        ):
            self.improper_submission.make_bag(Path(temp_dir), ["md5"])

    @patch("recordtransfer.models.UploadSession.copy_session_uploads")
    @patch("recordtransfer.models.Submission.remove_bag")
    def test_create_bag_exception_if_missing_file(
        self, remove_bag_mock: MagicMock, copy_uploads_mock: MagicMock
    ) -> None:
        """Test that an exception is thrown if there are missing files."""
        copy_uploads_mock.side_effect = self._create_new_files_MISSING

        with (
            self.assertRaises(FileNotFoundError),
            TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir,
        ):
            self.submission.make_bag(Path(temp_dir), ["md5"])

        # Check that the Bag is removed after an error
        remove_bag_mock.assert_called_once()

    @patch("upload.models.UploadSession.copy_session_uploads")
    @patch("recordtransfer.models.Submission.remove_bag")
    @patch("bagit.Bag.is_valid")
    def test_create_new_exception_if_bag_invalid(
        self, bag_valid_mock: MagicMock, remove_bag_mock: MagicMock, copy_uploads_mock: MagicMock
    ) -> None:
        """Test creating a new Bag that ends up being invalid."""
        copy_uploads_mock.side_effect = self._create_new_files_OK
        bag_valid_mock.return_value = False

        with (
            self.assertRaises(bagit.BagValidationError),
            TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir,
        ):
            self.submission.make_bag(Path(temp_dir), ["md5"])

        # Check that the Bag is removed after an error
        remove_bag_mock.assert_called_once()

    @patch("upload.models.UploadSession.copy_session_uploads")
    def test_create_new_bag(self, copy_uploads_mock: MagicMock) -> None:
        """Test creating a new Bag when one does not exist."""
        copy_uploads_mock.side_effect = self._create_new_files_OK

        with TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir:
            temp_dir_path = Path(temp_dir)

            bag = self.submission.make_bag(temp_dir_path, ["md5"])

            copy_uploads_mock.assert_called_once_with(temp_dir)

            self.assertTrue(temp_dir_path.exists())
            self.assertTrue(bag.is_valid())
            self.assertTrue((temp_dir_path / "data").exists())
            self.assertTrue((temp_dir_path / "data" / "hello.txt").exists())
            self.assertTrue((temp_dir_path / "data" / "world.txt").exists())
            self.assertTrue((temp_dir_path / "manifest-md5.txt").exists())
            # Read all non-empty lines in manifest file
            manifest_lines = list(
                filter(None, Path(temp_dir_path / "manifest-md5.txt").read_text().split("\n"))
            )
            self.assertEqual(len(manifest_lines), 2)
            self.assertIn(f"{self.HELLO_FILE_MD5}  data/hello.txt", manifest_lines)
            self.assertIn(f"{self.WORLD_FILE_MD5}  data/world.txt", manifest_lines)

    @patch("upload.models.UploadSession.copy_session_uploads")
    def test_create_new_bag_multiple_algorithms(self, copy_uploads_mock: MagicMock) -> None:
        """Test creating a new Bag with multiple checksum algorithms."""
        copy_uploads_mock.side_effect = self._create_new_files_OK

        with TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir:
            temp_dir_path = Path(temp_dir)

            self.submission.make_bag(temp_dir_path, ["md5", "sha1", "sha256"])

            self.assertTrue(temp_dir_path.exists())
            self.assertTrue((temp_dir_path / "manifest-md5.txt").exists())
            self.assertTrue((temp_dir_path / "manifest-sha1.txt").exists())
            self.assertTrue((temp_dir_path / "manifest-sha256.txt").exists())

    @patch("upload.models.UploadSession.get_permanent_uploads")
    @patch("upload.models.UploadSession.copy_session_uploads")
    def test_update_existing_bag(
        self, copy_uploads_mock: MagicMock, perm_upload_mock: MagicMock
    ) -> None:
        """Test the case where the permanent files match what's in the bag."""
        copy_uploads_mock.side_effect = self._create_new_files_OK

        perm_upload_mock.return_value = [
            self.test_perm_file_expected_1,
            self.test_perm_file_expected_2,
        ]

        with TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Make a bag first
            self.submission.make_bag(temp_dir_path, ["md5"])

            # Check the first title
            self.assertIn(
                "accessionTitle: My Test Title",
                (temp_dir_path / "bag-info.txt").read_text(),
            )

            # Store the modification time of the hello.txt file
            mod_time_before = (temp_dir_path / "data" / "hello.txt").stat().st_mtime

            # Change the accession title (so there's something to update in the bag)
            self.metadata.accession_title = "New Title"
            self.metadata.save()

            # Update the bag, and be sure bagit.make_bag is not called
            with patch("bagit.make_bag") as make_bag_mock:
                self.submission.make_bag(temp_dir_path, ["md5"])
                make_bag_mock.assert_not_called()

            # Check that the bag's metadata was updated
            self.assertIn(
                "accessionTitle: New Title",
                (temp_dir_path / "bag-info.txt").read_text(),
            )

            # Check that the modification time of the file was not changed
            mod_time_after = (temp_dir_path / "data" / "hello.txt").stat().st_mtime

            self.assertEqual(mod_time_before, mod_time_after)

    @patch("upload.models.UploadSession.get_permanent_uploads")
    @patch("upload.models.UploadSession.copy_session_uploads")
    def test_update_existing_bag_files_differ(
        self, copy_uploads_mock: MagicMock, perm_upload_mock: MagicMock
    ) -> None:
        """Test the case where the permanent files do not match what's in the bag."""
        copy_uploads_mock.side_effect = self._create_new_files_OK

        with TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Make a bag first
            self.submission.make_bag(temp_dir_path, ["md5"])

            # Return two unexpected files
            perm_upload_mock.return_value = [
                self.test_perm_file_unexpected_1,
                self.test_perm_file_unexpected_2,
            ]

            # Try to re-make the bag. The permanent uploads do not match so the Bag will be
            # re-created. Ensure bagit.make_bag is called again by mocking it this time
            with patch("bagit.make_bag") as make_bag_mock:
                self.submission.make_bag(temp_dir_path, ["md5"])
                make_bag_mock.assert_called_once()

            self.assertEqual(copy_uploads_mock.call_count, 2)

    @patch("upload.models.UploadSession.get_permanent_uploads")
    @patch("upload.models.UploadSession.copy_session_uploads")
    @patch("bagit.Bag")
    def test_update_existing_bag_exception(
        self, bag_mock: MagicMock, copy_uploads_mock: MagicMock, perm_upload_mock: MagicMock
    ) -> None:
        """Test the case where a BagError is thrown when trying to update the Bag."""
        copy_uploads_mock.side_effect = self._create_new_files_OK

        with TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Make a bag first with MD5 checksums
            self.submission.make_bag(temp_dir_path, ["md5"])

            # Return two expected files
            perm_upload_mock.return_value = [
                self.test_perm_file_expected_1,
                self.test_perm_file_expected_2,
            ]

            bag_mock.side_effect = bagit.BagError("Expected bagit.txt does not exist")

            # Try to re-make the bag. There will be a BagError, so the Bag will be re-generated
            # Ensure bagit.make_bag is called again by mocking it this time
            with patch("bagit.make_bag") as make_bag_mock:
                self.submission.make_bag(temp_dir_path, ["md5"])
                make_bag_mock.assert_called_once()

            self.assertEqual(copy_uploads_mock.call_count, 2)

    @patch("upload.models.UploadSession.get_permanent_uploads")
    @patch("upload.models.UploadSession.copy_session_uploads")
    def test_update_existing_bag_algorithms_differ(
        self, copy_uploads_mock: MagicMock, perm_upload_mock: MagicMock
    ) -> None:
        """Test the case where different checksums are requested for a Bag."""
        copy_uploads_mock.side_effect = self._create_new_files_OK

        with TemporaryDirectory(dir=settings.TEMP_STORAGE_FOLDER) as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Make a bag first with MD5 checksums
            self.submission.make_bag(temp_dir_path, ["md5"])

            # Return two expected files
            perm_upload_mock.return_value = [
                self.test_perm_file_expected_1,
                self.test_perm_file_expected_2,
            ]

            # Try to re-make the bag. The algorithms do not match so the Bag will be re-created
            self.submission.make_bag(temp_dir_path, ["sha1", "sha256"])

            self.assertEqual(copy_uploads_mock.call_count, 2)
            self.assertTrue((temp_dir_path / "manifest-sha1.txt").exists())
            self.assertTrue((temp_dir_path / "manifest-sha256.txt").exists())


class TestInProgressSubmission(TestCase):
    """Tests for the InProgressSubmission model."""

    def setUp(self) -> None:
        """Set up test."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session()
        self.in_progress = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.ACCEPT_LEGAL.value,
            step_data=b"test data",
            title="Test Submission",
            upload_session=self.upload_session,
        )

    def test_clean_invalid_step(self) -> None:
        """Test clean method with an invalid step."""
        self.in_progress.current_step = "INVALID_STEP"
        with self.assertRaises(ValidationError):
            self.in_progress.clean()

    def test_upload_session_expires_at(self) -> None:
        """Test upload_session_expires_at method."""
        self.assertEqual(
            self.in_progress.upload_session_expires_at, self.upload_session.expires_at
        )

    def test_upload_session_expires_at_no_session(self) -> None:
        """Test upload_session_expires_at method when there is no upload session."""
        self.in_progress.upload_session = None
        self.assertIsNone(self.in_progress.upload_session_expires_at)

    @patch("recordtransfer.models.UploadSession.is_expired", new_callable=PropertyMock)
    def test_upload_session_expired(self, mock_expired: PropertyMock) -> None:
        """Test upload_session_expired property."""
        mock_expired.return_value = True
        self.assertTrue(self.in_progress.upload_session_expired)

        mock_expired.return_value = False
        self.assertFalse(self.in_progress.upload_session_expired)

        self.in_progress.upload_session = None
        self.assertFalse(self.in_progress.upload_session_expired)

    @patch("upload.models.UploadSession.expires_soon", new_callable=PropertyMock)
    def test_upload_session_expires_soon(self, mock_expires_soon: PropertyMock) -> None:
        """Test upload_session_expires_soon property."""
        mock_expires_soon.return_value = True
        self.assertTrue(self.in_progress.upload_session_expires_soon)

        mock_expires_soon.return_value = False
        self.assertFalse(self.in_progress.upload_session_expires_soon)

        self.in_progress.upload_session = None
        self.assertFalse(self.in_progress.upload_session_expires_soon)

    def test_get_resume_url(self) -> None:
        """Test the get_resume_url method."""
        expected_url = f"{reverse('recordtransfer:submit')}?resume={self.in_progress.uuid}"
        self.assertEqual(self.in_progress.get_resume_url(), expected_url)

    def test_get_delete_url(self) -> None:
        """Test the get_delete_url method."""
        expected_url = reverse(
            "recordtransfer:delete_in_progress_submission_modal",
            kwargs={"uuid": self.in_progress.uuid},
        )
        self.assertEqual(self.in_progress.get_delete_url(), expected_url)

    def test_reset_reminder_email_sent_flag_true(self) -> None:
        """Test reset_reminder_email_sent method when the flag is True."""
        self.in_progress.reminder_email_sent = True
        self.in_progress.reset_reminder_email_sent()
        self.assertFalse(self.in_progress.reminder_email_sent)

    def test_reset_reminder_email_sent_flag_false(self) -> None:
        """Test reset_reminder_email_sent method when the flag is already False."""
        self.in_progress.reminder_email_sent = False
        self.in_progress.reset_reminder_email_sent()
        self.assertFalse(self.in_progress.reminder_email_sent)

    def test_str(self) -> None:
        """Test the string representation of the InProgressSubmission."""
        session_token = (
            self.in_progress.upload_session.token if self.in_progress.upload_session else "None"
        )
        expected_str = (
            f"In-Progress Submission by {self.user} "
            f"(Title: {self.in_progress.title} | Session: {session_token})"
        )
        self.assertEqual(str(self.in_progress), expected_str)


class TestSiteSetting(TestCase):
    """Tests for the SiteSetting model."""

    def setUp(self) -> None:
        """Set up test."""
        # Create test settings
        self.string_setting = SiteSetting.objects.create(
            key="TEST_STRING_SETTING",
            value="test string value",
            value_type=SiteSettingType.STR,
        )

        self.int_setting = SiteSetting.objects.create(
            key="TEST_INT_SETTING",
            value="42",
            value_type=SiteSettingType.INT,
        )

        # Clear cache since creation causes cache to be set. We want to control cache state in
        # tests.
        cache.clear()

    def test_set_cache_string_value(self) -> None:
        """Test caching a string value."""
        test_value = "cached string value"
        self.string_setting.set_cache(test_value)

        cached_value = cache.get(self.string_setting.key)
        self.assertEqual(cached_value, test_value)

    def test_set_cache_int_value(self) -> None:
        """Test caching an integer value."""
        test_value = 123
        self.int_setting.set_cache(test_value)

        cached_value = cache.get(self.int_setting.key)
        self.assertEqual(cached_value, test_value)

    def test_get_value_str_from_cache(self) -> None:
        """Test getting a string value from cache."""
        # Set cache value directly
        cache.set("TEST_STRING_SETTING", "cached value")

        # Create mock key
        mock_key = MagicMock()
        mock_key.name = "TEST_STRING_SETTING"

        result = SiteSetting.get_value_str(mock_key)
        self.assertEqual(result, "cached value")

    def test_get_value_str_from_database(self) -> None:
        """Test getting a string value from database when not cached."""
        # Ensure cache is empty
        cache.delete("TEST_STRING_SETTING")

        # Mock the Key enum
        mock_key = MagicMock()
        mock_key.name = "TEST_STRING_SETTING"

        with patch.object(SiteSetting.objects, "get", return_value=self.string_setting):
            result = SiteSetting.get_value_str(mock_key)
            self.assertEqual(result, "test string value")

    def test_get_value_str_wrong_type_raises_validation_error(self) -> None:
        """Test that getting a string value for an integer setting raises ValidationError."""
        mock_key = MagicMock()
        mock_key.name = "TEST_INT_SETTING"

        with (
            patch.object(SiteSetting.objects, "get", return_value=self.int_setting),
            self.assertRaises(ValidationError),
        ):
            SiteSetting.get_value_str(mock_key)

    def test_get_value_int_from_cache(self) -> None:
        """Test getting an integer value from cache."""
        # Set cache value
        cache.set("TEST_INT_SETTING", 99)

        mock_key = MagicMock()
        mock_key.name = "TEST_INT_SETTING"

        result = SiteSetting.get_value_int(mock_key)
        self.assertEqual(result, 99)

    def test_get_value_int_from_database(self) -> None:
        """Test getting an integer value from database when not cached."""
        # Ensure cache is empty
        cache.delete("TEST_INT_SETTING")

        mock_key = MagicMock()
        mock_key.name = "TEST_INT_SETTING"

        with patch.object(SiteSetting.objects, "get", return_value=self.int_setting):
            result = SiteSetting.get_value_int(mock_key)
            self.assertEqual(result, 42)

    def test_get_value_int_wrong_type_raises_validation_error(self) -> None:
        """Test that getting an int value for a string setting raises ValidationError."""
        mock_key = MagicMock()
        mock_key.name = "TEST_STRING_SETTING"

        with (
            patch.object(SiteSetting.objects, "get", return_value=self.string_setting),
            self.assertRaises(ValidationError),
        ):
            SiteSetting.get_value_int(mock_key)

    def test_get_value_int_invalid_string_value(self) -> None:
        """Test getting int value when database contains invalid integer string."""
        invalid_int_setting = SiteSetting.objects.create(
            key="TEST_INVALID_INT",
            value="not a number",
            value_type=SiteSettingType.INT,
        )

        mock_key = MagicMock()
        mock_key.name = "TEST_INVALID_INT"

        with (
            patch.object(SiteSetting.objects, "get", return_value=invalid_int_setting),
            self.assertRaises(ValueError),
        ):
            SiteSetting.get_value_int(mock_key)

    def test_get_value_str_with_cached_none_value(self) -> None:
        """Test that get_value_str doesn't query database when None is cached."""
        cache.set("TEST_STRING_SETTING", None)

        mock_key = MagicMock()
        mock_key.name = "TEST_STRING_SETTING"

        # Mock the database query to ensure it's not called
        with patch.object(SiteSetting.objects, "get") as mock_get:
            result = SiteSetting.get_value_str(mock_key)
            self.assertIsNone(result)
            # Verify database was not queried
            mock_get.assert_not_called()

    def test_get_value_int_with_cached_none_value(self) -> None:
        """Test that get_value_int doesn't query database when None is cached."""
        cache.set("TEST_INT_SETTING", None)

        mock_key = MagicMock()
        mock_key.name = "TEST_INT_SETTING"

        # Mock the database query to ensure it's not called
        with patch.object(SiteSetting.objects, "get") as mock_get:
            result = SiteSetting.get_value_int(mock_key)
            self.assertIsNone(result)
            # Verify database was not queried
            mock_get.assert_not_called()

    def test_get_value_str_cache_miss_queries_database(self) -> None:
        """Test that get_value_str queries database when value is not cached."""
        # Clear cache to ensure cache miss
        cache.delete("TEST_STRING_SETTING")

        mock_key = MagicMock()
        mock_key.name = "TEST_STRING_SETTING"

        # Mock the database query
        with patch.object(
            SiteSetting.objects, "get", return_value=self.string_setting
        ) as mock_get:
            result = SiteSetting.get_value_str(mock_key)
            self.assertEqual(result, "test string value")
            # Verify database was queried exactly once
            mock_get.assert_called_once_with(key="TEST_STRING_SETTING")

    def test_get_value_int_cache_miss_queries_database(self) -> None:
        """Test that get_value_int queries database when value is not cached."""
        # Clear cache to ensure cache miss
        cache.delete("TEST_INT_SETTING")

        mock_key = MagicMock()
        mock_key.name = "TEST_INT_SETTING"

        # Mock the database query
        with patch.object(SiteSetting.objects, "get", return_value=self.int_setting) as mock_get:
            result = SiteSetting.get_value_int(mock_key)
            self.assertEqual(result, 42)
            # Verify database was queried exactly once
            mock_get.assert_called_once_with(key="TEST_INT_SETTING")

    def test_post_save_signal_updates_cache_string(self) -> None:
        """Test that the post_save signal updates cache for string values on update, not
        creation.
        """
        # Create a new setting (triggers post_save with created=True)
        new_setting = SiteSetting.objects.create(
            key="NEW_STRING_SETTING",
            value="new value",
            value_type=SiteSettingType.STR,
        )

        # Check that value is NOT cached on creation
        cached_value = cache.get("NEW_STRING_SETTING")
        self.assertIsNone(cached_value)

        # Update the setting (triggers post_save with created=False)
        new_setting.value = "updated value"
        new_setting.save()

        # Check that value is cached on update
        cached_value = cache.get("NEW_STRING_SETTING")
        self.assertEqual(cached_value, "updated value")

    def test_post_save_signal_updates_cache_int(self) -> None:
        """Test that the post_save signal updates cache for integer values on update, not
        creation.
        """
        # Create a new setting (triggers post_save with created=True)
        new_setting = SiteSetting.objects.create(
            key="NEW_INT_SETTING",
            value="789",
            value_type=SiteSettingType.INT,
        )

        # Check that value is NOT cached on creation
        cached_value = cache.get("NEW_INT_SETTING")
        self.assertIsNone(cached_value)

        # Update the setting (triggers post_save with created=False)
        new_setting.value = "456"
        new_setting.save()

        # Check that value is cached as integer on update
        cached_value = cache.get("NEW_INT_SETTING")
        self.assertEqual(cached_value, 456)
        self.assertIsInstance(cached_value, int)

    def test_post_save_signal_with_invalid_int_raises_error(self) -> None:
        """Test that post_save signal with an invalid integer raises a ValidationError."""
        # Create setting with valid integer value
        new_setting = SiteSetting.objects.create(
            key="INVALID_INT_SETTING",
            value="123",
            value_type=SiteSettingType.INT,
        )

        with self.assertRaises(ValidationError):
            # Update with invalid integer value (triggers post_save with created=False)
            new_setting.value = "not a number"
            new_setting.save()

    def test_reset_to_default_with_default_value(self) -> None:
        """Test reset_to_default method when a default value exists."""
        # Mock the SiteSettingKey enum to have a default value
        mock_key = MagicMock()
        mock_key.default_value = "default test value"

        with patch("recordtransfer.models.SiteSettingKey") as mock_site_setting_key:
            mock_site_setting_key.__getitem__.return_value = mock_key
            # Change the setting value
            self.string_setting.value = "changed value"
            self.string_setting.save()

            # Reset to default
            self.string_setting.reset_to_default()

            # Check that it was reset
            self.assertEqual(self.string_setting.value, "default test value")

    def test_reset_to_default_key_does_not_exist(self) -> None:
        """Test reset_to_default method when key is not found in SiteSettingKey."""
        with (
            patch(
                "recordtransfer.models.SiteSettingKey.__getitem__",
                side_effect=KeyError("TEST_STRING_SETTING"),
            ),
            self.assertRaises(ValueError),
        ):
            self.string_setting.reset_to_default()

    def test_default_value_property_with_default(self) -> None:
        """Test default_value property when a default value exists."""
        mock_key = MagicMock()
        mock_key.default_value = "property default value"

        with patch("recordtransfer.models.SiteSettingKey") as mock_site_setting_key:
            mock_site_setting_key.__getitem__.return_value = mock_key
            result = self.string_setting.default_value
            self.assertEqual(result, "property default value")

    def test_default_value_property_key_does_not_exist(self) -> None:
        """Test default_value property when key is not found in SiteSettingKey."""
        with (
            patch(
                "recordtransfer.models.SiteSettingKey.__getitem__",
                side_effect=KeyError("TEST_STRING_SETTING"),
            ),
            self.assertRaises(ValueError),
        ):
            _ = self.string_setting.default_value


class TestUser(TestCase):
    """Tests for the User model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpassword123",
        )

    def test_full_name_property(self) -> None:
        """Test the full_name property."""
        self.assertEqual(self.user.full_name, "Test User")

        self.user.first_name = ""
        self.assertEqual(self.user.full_name, "User")

        self.user.first_name = "Test"
        self.user.last_name = ""
        self.assertEqual(self.user.full_name, "Test")

    def test_has_contact_info_false_when_missing_fields(self) -> None:
        """Test has_contact_info returns False when fields are missing."""
        self.assertFalse(self.user.has_contact_info)

    def test_has_contact_info_true_with_complete_info(self) -> None:
        """Test has_contact_info returns True with complete contact info."""
        self.user.phone_number = "+1 (555) 123-4567"
        self.user.address_line_1 = "123 Test Street"
        self.user.city = "Test City"
        self.user.province_or_state = "ON"
        self.user.postal_or_zip_code = "K1A 0A6"
        self.user.country = "CA"
        self.assertTrue(self.user.has_contact_info)

    def test_has_contact_info_with_other_province(self) -> None:
        """Test has_contact_info with 'Other' province selection."""
        self.user.phone_number = "+1 (555) 123-4567"
        self.user.address_line_1 = "123 Test Street"
        self.user.city = "Test City"
        self.user.province_or_state = "Other"
        self.user.postal_or_zip_code = "12345"
        self.user.country = "US"

        # Should be False without other_province_or_state
        self.assertFalse(self.user.has_contact_info)

        # Should be True with other_province_or_state filled
        self.user.other_province_or_state = "Custom Province"
        self.assertTrue(self.user.has_contact_info)


class TestJob(TestCase):
    """Tests for the Job model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpassword123",
        )

        self.job = Job.objects.create(
            name="Test Job",
            description="A test job for unit testing",
            start_time=timezone.now(),
            user_triggered=self.user,
            job_status=Job.JobStatus.NOT_STARTED,
        )

    def tearDown(self) -> None:
        """Clean up test data."""
        # Clean up any uploaded files
        if self.job.attached_file:
            self.job.attached_file.delete()

        Job.objects.all().delete()
        User.objects.all().delete()

    def test_has_file_without_attached_file(self) -> None:
        """Test has_file method when no file is attached."""
        self.assertFalse(self.job.has_file())

    def test_has_file_with_attached_file(self) -> None:
        """Test has_file method when a file is attached."""
        # Create a mock file
        mock_file = SimpleUploadedFile("test.txt", b"test content", content_type="text/plain")

        self.job.attached_file.save("test.txt", mock_file)

        self.assertTrue(self.job.has_file())

    def test_get_file_media_url_with_file(self) -> None:
        """Test get_file_media_url method when a file is attached."""
        mock_file = SimpleUploadedFile("test.txt", b"test content", content_type="text/plain")

        self.job.attached_file.save("test.txt", mock_file)

        # The method should return the URL of the attached file
        url = self.job.get_file_media_url()
        self.assertIsInstance(url, str)
        self.assertTrue(url.endswith("test.txt"))

    def test_get_file_media_url_without_file(self) -> None:
        """Test get_file_media_url method when no file is attached."""
        with self.assertRaises(FileNotFoundError) as context:
            self.job.get_file_media_url()

        expected_message = f"{self.job.name} does not exist in job {self.job.uuid}"
        self.assertEqual(str(context.exception), expected_message)

    def test_str_representation(self) -> None:
        """Test the string representation of the Job model."""
        expected_str = f"{self.job.name} (Created by {self.job.user_triggered})"
        self.assertEqual(str(self.job), expected_str)
