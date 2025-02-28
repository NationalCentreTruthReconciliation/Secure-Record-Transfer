from datetime import timezone as dttimezone
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from recordtransfer.enums import TransferStep
from recordtransfer.models import InProgressSubmission, UploadSession, User


class TestUploadSessionManager(TestCase):
    """Tests for the UploadSession manager."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session(user=self.user)

    # Tests for get_expirable method

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_expirable(self, mock_now: MagicMock) -> None:
        """Test when there are is an expirable upload session."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        # Create an in-progress submission associated with the upload session

        expirable_statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
        ]

        for status in expirable_statuses:
            self.upload_session.status = status
            self.upload_session.save()

        expirable_sessions = UploadSession.objects.get_expirable()
        self.assertIn(self.upload_session, expirable_sessions)

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_expirable_none_expired(self, mock_now: MagicMock) -> None:
        """Test that session which has not expired yet is not returned."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Set last upload interaction time to be greater than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time + timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        # Create an in-progress submission associated with the upload session
        InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

        expired_sessions = UploadSession.objects.get_expirable()
        self.assertFalse(expired_sessions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_expirable_no_in_progress_submission(self, mock_now: MagicMock) -> None:
        """Test that an expired upload session with no associated in-progress submission is not
        returned.
        """
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        expired_sessions = UploadSession.objects.get_expirable()
        self.assertFalse(expired_sessions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", -1)
    def test_get_expirable_expiry_disabled(self, mock_now: MagicMock) -> None:
        """Test when the upload session expiry feature is disabled."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Create an in-progress submission associated with the upload session
        InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        expirable_statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
        ]

        for status in expirable_statuses:
            self.upload_session.status = status
            self.upload_session.save()

            expired_sessions = UploadSession.objects.get_expirable()
            self.assertFalse(expired_sessions.exists())

    # Tests for get_deletable method

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_deletable_expired_status_session(self) -> None:
        """Test when there are is an upload session with the EXPIRED status, without an
        associated InProgressSubmission.
        """
        # Set the upload session status to EXPIRED
        self.upload_session.status = UploadSession.SessionStatus.EXPIRED
        self.upload_session.save()

        # Verify the session is returned by get_deletable
        deletable_sessions = UploadSession.objects.get_deletable()
        self.assertIn(self.upload_session, deletable_sessions)

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_deletable_session_has_expired(self, mock_now: MagicMock) -> None:
        """Test when there are is an upload session of either the CREATED or UPLOADING status that
        has expired, without an associated InProgressSubmission.
        """
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        deletable_statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
        ]

        for status in deletable_statuses:
            self.upload_session.status = status
            self.upload_session.save()

            deletable_sessions = UploadSession.objects.get_deletable()
            self.assertIn(self.upload_session, deletable_sessions)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_deletable_with_in_progress_submission(self) -> None:
        """Test when an expired upload session has an associated in-progress submission."""
        # Set the upload session status to EXPIRED
        self.upload_session.status = UploadSession.SessionStatus.EXPIRED
        self.upload_session.save()

        # Create an in-progress submission associated with the upload session
        InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

        # Verify the session is not returned by get_deletable
        deletable_sessions = UploadSession.objects.get_deletable()
        self.assertNotIn(self.upload_session, deletable_sessions)
        self.assertFalse(deletable_sessions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_deletable_session_has_expired_with_in_progress_submission(
        self, mock_now: MagicMock
    ) -> None:
        """Test when an upload session of either the CREATED or UPLOADING status has expired and
        has an associated in-progress submission.
        """
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Create an in-progress submission associated with the upload session
        InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        deletable_statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
        ]

        for status in deletable_statuses:
            self.upload_session.status = status
            self.upload_session.save()

            deletable_sessions = UploadSession.objects.get_deletable()
            self.assertFalse(deletable_sessions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    def test_get_deletable_session_has_not_expired_with_in_progress_submission(
        self, mock_now: MagicMock
    ) -> None:
        """Test when an upload session of either the CREATED or UPLOADING status has not expired
        yet and has an associated in-progress submission.
        """
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
        )

        # Create an in-progress submission associated with the upload session
        InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

        # Set last upload interaction time to be greater than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time + timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        deletable_statuses = [
            UploadSession.SessionStatus.CREATED,
            UploadSession.SessionStatus.UPLOADING,
        ]

        for status in deletable_statuses:
            self.upload_session.status = status
            self.upload_session.save()

            deletable_sessions = UploadSession.objects.get_deletable()
            self.assertFalse(deletable_sessions.exists())

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", -1)
    def test_get_deletable_expiry_disabled(self) -> None:
        """Test when the upload session expiry feature is disabled."""
        # Set the upload session status to EXPIRED
        self.upload_session.status = UploadSession.SessionStatus.EXPIRED
        self.upload_session.save()

        deletable_sessions = UploadSession.objects.get_deletable()
        self.assertFalse(deletable_sessions.exists())


class TestInProgressSubmissionManager(TestCase):
    """Tests for the InProgressSubmission manager."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session(user=self.user)
        self.in_progress_submission = InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=TransferStep.UPLOAD_FILES.value,
        )

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 10)
    def test_one_expiring(self, mock_now: MagicMock) -> None:
        """Test when there is an expiring submission."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=(
                settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
                - settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
            )
        )

        # Set last upload interaction time to be less than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time - timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertIn(self.in_progress_submission, expiring_submissions)

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 10)
    def test_none_expiring(self, mock_now: MagicMock) -> None:
        """Test when there are no expiring submissions."""
        # Setup mock time
        mock_now.return_value = timezone.datetime(2023, 10, 10, 12, 0, 0, tzinfo=dttimezone.utc)
        cutoff_time = mock_now() - timezone.timedelta(
            minutes=(
                settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES
                - settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES
            )
        )

        # Set last upload interaction time to be greater than cutoff time
        self.upload_session.last_upload_interaction_time = cutoff_time + timezone.timedelta(
            minutes=1
        )
        self.upload_session.save()

        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertFalse(expiring_submissions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", -1)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 10)
    def test_upload_session_expiry_disabled(self, mock_now: MagicMock) -> None:
        """Test when the upload session expiry feature is disabled."""
        # Test get_expiring method
        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertFalse(expiring_submissions.exists())

    @patch("django.utils.timezone.now")
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 30)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", -1)
    def test_upload_session_expiry_reminder_disabled(self, mock_now: MagicMock) -> None:
        """Test when the upload session expiry reminder feature is disabled."""
        # Test get_expiring method
        expiring_submissions = InProgressSubmission.objects.get_expiring_without_reminder()
        self.assertFalse(expiring_submissions.exists())
