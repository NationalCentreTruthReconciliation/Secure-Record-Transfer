from datetime import timezone as dttimezone
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone

from recordtransfer.enums import SubmissionStep
from recordtransfer.models import InProgressSubmission, UploadSession, User
from recordtransfer.wizard_storage import initial_wizard_data


class TestInProgressSubmissionManager(TestCase):
    """Tests for the InProgressSubmission manager."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.user = User.objects.create(username="testuser", password="password")
        self.upload_session = UploadSession.new_session(user=self.user)
        self.in_progress_submission = InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=SubmissionStep.UPLOAD_FILES.value,
        )

    def test_get_interacted_excludes_only_pristine_canonical_drafts(self) -> None:
        """Legacy and changed drafts are visible, but automatic untouched drafts are not."""
        first_step = SubmissionStep.ACCEPT_LEGAL.value
        pristine = InProgressSubmission.objects.create(
            user=self.user,
            current_step=first_step,
            step_data=initial_wizard_data(first_step),
        )
        interacted = InProgressSubmission.objects.create(
            user=self.user,
            current_step=first_step,
            step_data=initial_wizard_data(first_step),
        )
        interacted.step_data["wizard"]["step_data"] = {
            first_step: {f"{first_step}-agreement_accepted": ["on"]}
        }
        interacted.save(update_fields=["step_data"])

        drafts = InProgressSubmission.objects.get_interacted()

        self.assertNotIn(pristine, drafts)
        self.assertIn(interacted, drafts)
        self.assertIn(self.in_progress_submission, drafts)

    @override_settings(IN_PROGRESS_SUBMISSION_PRISTINE_RETENTION_MINUTES=60)
    def test_get_stale_pristine_uses_interaction_and_age(self) -> None:
        """Only untouched canonical drafts older than retention are cleanup candidates."""
        first_step = SubmissionStep.ACCEPT_LEGAL.value
        old_pristine = InProgressSubmission.objects.create(
            user=self.user,
            current_step=first_step,
            step_data=initial_wizard_data(first_step),
        )
        old_interacted = InProgressSubmission.objects.create(
            user=self.user,
            current_step=first_step,
            step_data=initial_wizard_data(first_step),
        )
        old_interacted.step_data["wizard"]["step_data"] = {first_step: {"field": ["value"]}}
        old_interacted.save(update_fields=["step_data"])
        old_time = timezone.now() - timezone.timedelta(minutes=61)
        InProgressSubmission.objects.filter(pk__in=[old_pristine.pk, old_interacted.pk]).update(
            last_updated=old_time
        )

        stale = InProgressSubmission.objects.get_stale_pristine()

        self.assertIn(old_pristine, stale)
        self.assertNotIn(old_interacted, stale)
        self.assertNotIn(self.in_progress_submission, stale)

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
