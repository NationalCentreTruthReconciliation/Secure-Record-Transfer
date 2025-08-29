from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from freezegun import freeze_time

from recordtransfer.jobs import (
    check_expiring_in_progress_submissions,
    cleanup_expired_sessions,
    create_downloadable_bag,
    move_uploads_and_send_emails,
)
from recordtransfer.models import Job, Submission, UploadSession, User


class TestCreateDownloadableBag(TestCase):
    """Tests the functionality of the create_downloadable_bag job."""

    def setUp(self) -> None:
        """Set up common test fixtures."""
        self.mock_submission = MagicMock(spec_set=Submission)
        self.mock_submission.__str__.return_value = "Test Submission"  # type: ignore
        self.mock_submission.bag_name = "test-bag"

        self.mock_user = MagicMock(spec_set=User)
        self.mock_user.__str__.return_value = "John Doe"  # type: ignore
        self.mock_user.username = "TestUser"

        self.mock_job = MagicMock(spec_set=Job)
        self.mock_job.pk = 8

        self.mock_temporarydirectory = MagicMock()
        self.mock_temporarydirectory.__enter__.return_value = "/tmp/my-bag"
        self.mock_temporarydirectory.__exit__.return_value = None

    @freeze_time(datetime(2025, 1, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
    @override_settings(BAG_CHECKSUMS=["sha1"])
    @patch("recordtransfer.jobs.Job")
    @patch("tempfile.TemporaryDirectory")
    def test_bag_creation_success(
        self, mock_temp_dir_class: MagicMock, mock_job_class: MagicMock
    ) -> None:
        """Test that a bag gets created successfully (happy path)."""
        mock_temp_dir_class.return_value = self.mock_temporarydirectory

        mock_job_class.JobStatus = Job.JobStatus
        mock_job_class.return_value = self.mock_job

        # Successful make_bag call
        self.mock_submission.make_bag.return_value = None

        with (
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("tempfile.TemporaryFile"),
            patch("zipfile.ZipFile"),
            patch("recordtransfer.jobs.JobLogHandler"),
            patch("recordtransfer.jobs.LOGGER"),
            patch("recordtransfer.utils.zip_directory"),
        ):
            create_downloadable_bag(self.mock_submission, self.mock_user)

        # Verify job creation
        mock_job_class.assert_called_once()
        call_kwargs = mock_job_class.call_args[1]
        self.assertEqual(call_kwargs["name"], "Generate Downloadable Bag for Test Submission")
        self.assertIn("John Doe triggered this job", call_kwargs["description"])
        self.assertEqual(
            call_kwargs["start_time"],
            datetime(2025, 1, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)),
        )
        self.assertEqual(call_kwargs["user_triggered"], self.mock_user)
        self.assertEqual(call_kwargs["job_status"], Job.JobStatus.IN_PROGRESS)

        # Verify submission make_bag called correctly
        self.mock_submission.make_bag.assert_called_with(
            Path("/tmp/my-bag"),
            algorithms=["sha1"],
        )

        # Verify job completed
        self.assertEqual(self.mock_job.job_status, Job.JobStatus.COMPLETE)

    @freeze_time(datetime(2025, 2, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
    @override_settings(BAG_CHECKSUMS=["sha1"])
    @patch("recordtransfer.jobs.Job")
    @patch("tempfile.TemporaryDirectory")
    def test_bag_creation_error_missing_files(
        self, mock_temp_dir_class: MagicMock, mock_job_class: MagicMock
    ) -> None:
        """Test that a bag is not created when files are missing."""
        mock_temp_dir_class.return_value = self.mock_temporarydirectory

        mock_job_class.JobStatus = Job.JobStatus
        mock_job_class.return_value = self.mock_job

        self.mock_submission.make_bag.side_effect = FileNotFoundError("missing files")

        with (
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("recordtransfer.jobs.JobLogHandler"),
            patch("recordtransfer.jobs.LOGGER"),
            patch("recordtransfer.utils.zip_directory"),
            patch("tempfile.TemporaryFile"),
            patch("zipfile.ZipFile"),
        ):
            create_downloadable_bag(self.mock_submission, self.mock_user)

        # Verify submission make_bag called correctly
        self.mock_submission.make_bag.assert_called_with(
            Path("/tmp/my-bag"),
            algorithms=["sha1"],
        )

        # Verify job completed
        self.assertEqual(self.mock_job.job_status, Job.JobStatus.FAILED)

    @freeze_time(datetime(2025, 3, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
    @override_settings(BAG_CHECKSUMS=["sha1"])
    @patch("recordtransfer.jobs.Job")
    @patch("tempfile.TemporaryDirectory")
    def test_bag_creation_error_generic_err(
        self, mock_temp_dir_class: MagicMock, mock_job_class: MagicMock
    ) -> None:
        """Test that a bag is not created when some error occured in make_bag."""
        mock_temp_dir_class.return_value = self.mock_temporarydirectory

        mock_job_class.JobStatus = Job.JobStatus
        mock_job_class.return_value = self.mock_job

        self.mock_submission.make_bag.side_effect = ValueError("no metadata")

        with (
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("recordtransfer.jobs.JobLogHandler"),
            patch("recordtransfer.jobs.LOGGER"),
            patch("recordtransfer.utils.zip_directory"),
            patch("tempfile.TemporaryFile"),
            patch("zipfile.ZipFile"),
        ):
            create_downloadable_bag(self.mock_submission, self.mock_user)

        # Verify submission make_bag called correctly
        self.mock_submission.make_bag.assert_called_with(
            Path("/tmp/my-bag"),
            algorithms=["sha1"],
        )

        # Verify job failure
        self.assertEqual(self.mock_job.job_status, Job.JobStatus.FAILED)

    @freeze_time(datetime(2025, 3, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
    @override_settings(BAG_CHECKSUMS="sha1")
    @override_settings(TEMP_STORAGE_FOLDER="/tmp")
    @patch("recordtransfer.jobs.Job")
    @patch("recordtransfer.jobs.File")
    @patch("recordtransfer.utils.zip_directory")
    @patch("zipfile.ZipFile")
    @patch("tempfile.TemporaryFile")
    @patch("tempfile.TemporaryDirectory")
    def test_attach_zipped_bag_to_job(
        self,
        mock_temp_dir_class: MagicMock,
        mock_temp_file_class: MagicMock,
        mock_zip_class: MagicMock,
        mock_zip_directory: MagicMock,
        mock_file_class: MagicMock,
        mock_job_class: MagicMock,
    ) -> None:
        """Test that the submission is bagged, zipped, and attached to job."""
        mock_temp_dir_class.return_value = self.mock_temporarydirectory

        mock_job_class.JobStatus = Job.JobStatus
        mock_job_class.return_value = self.mock_job

        # Mock calling TemporaryFile()
        mock_temp_file_instance = MagicMock()
        mock_temp_file_instance.name = "temp_file.zip"
        mock_temp_file_class.return_value.__enter__.return_value = mock_temp_file_instance

        # Mock calling zipfile.ZipFile()
        mock_zipfile_instance = MagicMock()
        mock_zip_class.return_value = mock_zipfile_instance

        # Mock calling File()
        mock_file = MagicMock()
        mock_file_class.return_value = mock_file

        with (
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("recordtransfer.jobs.JobLogHandler"),
            patch("recordtransfer.jobs.LOGGER"),
        ):
            create_downloadable_bag(self.mock_submission, self.mock_user)

        # Verify zip creation
        mock_zip_directory.assert_called_with("/tmp/my-bag", mock_zipfile_instance)

        # Verify file saved to model
        self.mock_job.attached_file.save.assert_called_once_with(
            "test-bag.zip", mock_file, save=True
        )

        # Verify job completed
        self.assertEqual(self.mock_job.job_status, Job.JobStatus.COMPLETE)

    @freeze_time(datetime(2025, 3, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
    @override_settings(BAG_CHECKSUMS="sha1")
    @override_settings(TEMP_STORAGE_FOLDER="/tmp")
    @patch("recordtransfer.jobs.Job")
    @patch("recordtransfer.jobs.File")
    @patch("recordtransfer.utils.zip_directory")
    @patch("zipfile.ZipFile")
    @patch("tempfile.TemporaryFile")
    @patch("tempfile.TemporaryDirectory")
    def test_attach_zipped_bag_to_job_failure(
        self,
        mock_temp_dir_class: MagicMock,
        mock_temp_file_class: MagicMock,
        mock_zip_class: MagicMock,
        mock_zip_directory: MagicMock,
        mock_file_class: MagicMock,
        mock_job_class: MagicMock,
    ) -> None:
        """Test that the job status is set correctly when an exception is raised."""
        mock_temp_dir_class.return_value = self.mock_temporarydirectory

        mock_job_class.JobStatus = Job.JobStatus
        mock_job_class.return_value = self.mock_job

        # Simulate no disk space left
        mock_temp_file_class.side_effect = OSError("Disk full")

        # Mock calling zipfile.ZipFile()
        mock_zipfile_instance = MagicMock()
        mock_zip_class.return_value = mock_zipfile_instance

        # Mock calling File()
        mock_file = MagicMock()
        mock_file_class.return_value = mock_file

        with (
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("recordtransfer.jobs.JobLogHandler"),
            patch("recordtransfer.jobs.LOGGER"),
        ):
            create_downloadable_bag(self.mock_submission, self.mock_user)

        # Verify zip was not created
        mock_zip_directory.assert_not_called()

        # Verify file was not saved
        self.mock_job.attached_file.save.assert_not_called()

        # Verify job failure
        self.assertEqual(self.mock_job.job_status, Job.JobStatus.FAILED)


class TestMoveUploadsAndSendEmailsJob(TestCase):
    """Tests for the move_uploads_and_send_emails job."""

    def setUp(self) -> None:
        """Create test data."""
        self.user = User.objects.create(username="testuser", password="svaE95EQW^")
        self.upload_session = UploadSession.new_session(user=self.user)
        self.submission = Submission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
        )
        return super().setUp()

    @patch("recordtransfer.jobs.send_your_submission_did_not_go_through")
    @patch("recordtransfer.jobs.send_thank_you_for_your_submission")
    @patch("recordtransfer.jobs.send_submission_creation_failure")
    @patch("recordtransfer.jobs.send_submission_creation_success")
    def test_move_one_upload(
        self,
        mock_creation_success: MagicMock,
        mock_creation_failure: MagicMock,
        mock_submit_success: MagicMock,
        mock_submit_failure: MagicMock,
    ) -> None:
        """Test moving one file."""
        self.upload_session.add_temp_file(SimpleUploadedFile("image.jpg", bytearray([1] * 1024)))

        temp_dir = Path(settings.TEMP_STORAGE_FOLDER) / self.upload_session.token
        perm_dir = Path(settings.UPLOAD_STORAGE_FOLDER) / self.upload_session.token

        # Temp dir should have one file
        self.assertEqual(1, sum(1 if item.is_file() else 0 for item in temp_dir.iterdir()))

        move_uploads_and_send_emails(self.submission, {})

        self.assertFalse(temp_dir.exists())
        self.assertTrue(perm_dir.exists())
        self.assertEqual(1, sum(1 if item.is_file() else 0 for item in perm_dir.iterdir()))
        self.assertEqual(UploadSession.SessionStatus.STORED, self.upload_session.status)
        mock_creation_success.assert_called_once()
        mock_submit_success.assert_called_once()

    @patch("recordtransfer.jobs.send_your_submission_did_not_go_through")
    @patch("recordtransfer.jobs.send_thank_you_for_your_submission")
    @patch("recordtransfer.jobs.send_submission_creation_failure")
    @patch("recordtransfer.jobs.send_submission_creation_success")
    def test_move_multiple_uploads(
        self,
        mock_creation_success: MagicMock,
        mock_creation_failure: MagicMock,
        mock_submit_success: MagicMock,
        mock_submit_failure: MagicMock,
    ) -> None:
        """Test moving multiple files."""
        for i in range(1, 11):
            self.upload_session.add_temp_file(
                SimpleUploadedFile(f"image-{i}.jpg", bytearray([1] * 1024))
            )

        temp_dir = Path(settings.TEMP_STORAGE_FOLDER) / self.upload_session.token
        perm_dir = Path(settings.UPLOAD_STORAGE_FOLDER) / self.upload_session.token

        # Temp dir should have ten files
        self.assertEqual(10, sum(1 if item.is_file() else 0 for item in temp_dir.iterdir()))

        move_uploads_and_send_emails(self.submission, {})

        self.assertFalse(temp_dir.exists())
        self.assertTrue(perm_dir.exists())
        self.assertEqual(10, sum(1 if item.is_file() else 0 for item in perm_dir.iterdir()))
        self.assertEqual(UploadSession.SessionStatus.STORED, self.upload_session.status)
        mock_creation_success.assert_called_once()
        mock_submit_success.assert_called_once()

    @patch("recordtransfer.jobs.send_your_submission_did_not_go_through")
    @patch("recordtransfer.jobs.send_thank_you_for_your_submission")
    @patch("recordtransfer.jobs.send_submission_creation_failure")
    @patch("recordtransfer.jobs.send_submission_creation_success")
    @patch.object(UploadSession, "make_uploads_permanent")
    def test_move_uploads_failure(
        self,
        mock_make_uploads_permanent: MagicMock,
        mock_creation_success: MagicMock,
        mock_creation_failure: MagicMock,
        mock_submit_success: MagicMock,
        mock_submit_failure: MagicMock,
    ) -> None:
        """Test the case when uploads can't be moved."""

        def copy_fail():
            self.upload_session.status = UploadSession.SessionStatus.COPYING_FAILED
            self.upload_session.save()

        # Set up the mock to call copy_fail each time it's called
        mock_make_uploads_permanent.side_effect = copy_fail

        self.upload_session.add_temp_file(SimpleUploadedFile("image.jpg", bytearray([1] * 1024)))

        move_uploads_and_send_emails(self.submission, {})

        # The function should have been called twice
        mock_make_uploads_permanent.assert_has_calls([call(), call()])
        self.assertEqual(UploadSession.SessionStatus.COPYING_FAILED, self.upload_session.status)
        mock_creation_failure.assert_called_once()
        mock_submit_failure.assert_called_once()

    @patch("recordtransfer.jobs.send_your_submission_did_not_go_through")
    @patch("recordtransfer.jobs.send_thank_you_for_your_submission")
    @patch("recordtransfer.jobs.send_submission_creation_failure")
    @patch("recordtransfer.jobs.send_submission_creation_success")
    @patch.object(UploadSession, "make_uploads_permanent")
    def test_move_uploads_succeed_second_try(
        self,
        mock_make_uploads_permanent: MagicMock,
        mock_creation_success: MagicMock,
        mock_creation_failure: MagicMock,
        mock_submit_success: MagicMock,
        mock_submit_failure: MagicMock,
    ) -> None:
        """Test the case when uploads can't be moved on first try but succeed on second try."""
        call_count = 0

        def mock_make_permanent():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                self.upload_session.status = UploadSession.SessionStatus.COPYING_FAILED
                self.upload_session.save()
            else:
                # Second call succeeds
                self.upload_session.status = UploadSession.SessionStatus.STORED
                self.upload_session.save()

        # Set up the mock to use our counting function
        mock_make_uploads_permanent.side_effect = mock_make_permanent

        self.upload_session.add_temp_file(SimpleUploadedFile("image.jpg", bytearray([1] * 1024)))

        move_uploads_and_send_emails(self.submission, {})

        # The function should have been called twice
        mock_make_uploads_permanent.assert_has_calls([call(), call()])
        self.assertEqual(UploadSession.SessionStatus.STORED, self.upload_session.status)
        mock_creation_success.assert_called_once()
        mock_submit_success.assert_called_once()

    @patch("recordtransfer.jobs.send_your_submission_did_not_go_through")
    @patch("recordtransfer.jobs.send_thank_you_for_your_submission")
    @patch("recordtransfer.jobs.send_submission_creation_failure")
    @patch("recordtransfer.jobs.send_submission_creation_success")
    @patch.object(UploadSession, "make_uploads_permanent")
    def test_no_uploads_to_move(
        self,
        mock_make_uploads_permanent: MagicMock,
        mock_creation_success: MagicMock,
        mock_creation_failure: MagicMock,
        mock_submit_success: MagicMock,
        mock_submit_failure: MagicMock,
    ) -> None:
        """Test that only the emails are sent when there are no uploads."""
        self.submission.upload_session = None
        self.submission.save()

        move_uploads_and_send_emails(self.submission, {})

        mock_make_uploads_permanent.assert_not_called()
        mock_creation_success.assert_called_once()
        mock_submit_success.assert_called_once()


class TestCheckExpiringInProgressSubmissions(TestCase):
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


class TestCleanupExpiredSessions(TestCase):
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

    @patch("recordtransfer.models.UploadSession.objects.get_deletable")
    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_expirable_session(
        self, mock_get_expirable: MagicMock, mock_get_deletable: MagicMock
    ) -> None:
        """Test when there's an expirable session."""
        # Setup mocks
        mock_session = MagicMock()

        mock_expirable_queryset = MagicMock()
        mock_expirable_queryset.__iter__.return_value = [mock_session]
        mock_expirable_queryset.count.return_value = 1
        mock_get_expirable.return_value.all.return_value = mock_expirable_queryset

        cleanup_expired_sessions()

        mock_session.expire.assert_called_once()
        mock_session.delete.assert_not_called()

    @patch("recordtransfer.models.UploadSession.objects.get_deletable")
    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_deletable_session(
        self, mock_get_expirable: MagicMock, mock_get_deletable: MagicMock
    ) -> None:
        """Test when there is a deletable session."""
        # Setup mocks
        mock_session = MagicMock()

        mock_deletable_queryset = MagicMock()
        mock_deletable_queryset.__iter__.return_value = [mock_session]
        mock_deletable_queryset.count.return_value = 1
        mock_get_deletable.return_value.all.return_value = mock_deletable_queryset

        cleanup_expired_sessions()

        mock_session.delete.assert_called_once()
        mock_session.expire.assert_not_called()

    @patch("recordtransfer.models.UploadSession.objects.get_expirable")
    def test_exception_handling(self, mock_get_expirable: MagicMock) -> None:
        """Test that exceptions are properly handled."""
        # Setup mock to raise an exception
        mock_get_expirable.side_effect = Exception("Test error")

        # Verify the exception is re-raised
        with self.assertRaises(Exception):
            cleanup_expired_sessions()
