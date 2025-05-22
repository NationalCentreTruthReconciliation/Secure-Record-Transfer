import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, cast
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _
from freezegun import freeze_time

from recordtransfer.constants import PAGINATE_QUERY_NAME
from recordtransfer.enums import SubmissionStep
from recordtransfer.models import (
    InProgressSubmission,
    Submission,
    SubmissionGroup,
    UploadSession,
    User,
)


@patch("recordtransfer.emails.send_user_account_updated.delay", lambda a, b: None)
@freeze_time(datetime(2025, 1, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
class TestUserProfileView(TestCase):
    def setUp(self):
        self.test_username = "testuser"
        self.test_first_name = "Test"
        self.test_last_name = "User"
        self.test_email = "testuser@example.com"
        self.test_current_password = "old_password"
        self.test_gets_notification_emails = True
        self.test_new_password = "new_password123"
        self.user = User.objects.create_user(
            username=self.test_username,
            first_name=self.test_first_name,
            last_name=self.test_last_name,
            email=self.test_email,
            password=self.test_current_password,
            gets_notification_emails=self.test_gets_notification_emails,
        )
        self.client.login(username="testuser", password="old_password")
        self.url = reverse("recordtransfer:user_profile")
        self.error_message = "There was an error updating your preferences. Please try again."
        self.success_message = "Preferences updated"
        self.password_change_success_message = "Password updated"

        # Table URLs
        self.submission_group_table_url = reverse("recordtransfer:submission_group_table")
        self.in_progress_table_url = reverse("recordtransfer:in_progress_submission_table")
        self.submission_table_url = reverse("recordtransfer:submission_table")

        # HTMX related
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        UploadSession.objects.all().delete()
        InProgressSubmission.objects.all().delete()
        SubmissionGroup.objects.all().delete()
        Submission.objects.all().delete()
        User.objects.all().delete()

    def _create_in_progress_submission(
        self,
        title: Optional[str] = None,
        user: Optional[User] = None,
        upload_session: Optional[UploadSession] = None,
    ) -> InProgressSubmission:
        """Create an InProgressSubmission for testing.

        Args:
            title: Title for the submission. Defaults to "Test Submission".
            user: User who owns the submission. Defaults to self.user.
            upload_session: Associated upload session. Defaults to
                creating a new session for the specified user.

        Returns:
            The newly created in-progress submission object.
        """
        if user is None:
            user = self.user

        if upload_session is None:
            upload_session = UploadSession.new_session(user=cast(User, user))

        if title is None:
            title = "Test Submission"

        return InProgressSubmission.objects.create(
            user=user,
            uuid=str(uuid.uuid4()),
            upload_session=upload_session,
            title=title,
        )

    def test_access_authenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")

    def test_access_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    ### Tests for Profile Details ###

    def test_valid_name_change(self):
        form_data = {
            "first_name": "New",
            "last_name": "Name",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_accented_name_change(self):
        form_data = {
            "first_name": "Áccéntéd",
            "last_name": "Námé",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_invalid_first_name(self):
        form_data = {
            "first_name": "123",
            "last_name": self.test_last_name,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_invalid_last_name(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": "123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_valid_notification_setting_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": False,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_invalid_notification_setting_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": self.test_gets_notification_emails,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_valid_password_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Password updated")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new_password123"))

    def test_wrong_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": "wrong_password",
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_passwords_do_not_match(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "new_password": "new_password123",
            "confirm_new_password": "different_password",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_same_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "new_password": self.test_current_password,
            "confirm_new_password": self.test_current_password,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_missing_current_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_missing_new_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_missing_confirm_new_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": True,
            "current_password": self.test_current_password,
            "new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_no_changes(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": self.test_gets_notification_emails,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_empty_form_submission(self):
        form_data = {}
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    ### Tests for All Tables ###
    def test_tables_require_htmx_request(self) -> None:
        """Test that all table views require HTMX headers."""
        for url in [
            self.submission_group_table_url,
            self.in_progress_table_url,
            self.submission_table_url,
        ]:
            response = self.client.get(url)  # No HTMX headers
            self.assertEqual(response.status_code, 400)

    ### Tests for In-Progress Submission Table ###

    def test_in_progress_submission_expires_at_no_expiry(self) -> None:
        """Test that the "Expires at" cell contains just a dash when the in-progress submission
        has no upload session, hence no expiry date.
        """
        # Create an in-progress submission without an upload session
        InProgressSubmission.objects.create(
            user=self.user,
            uuid=str(uuid.uuid4()),
            title="Test In-Progress Submission",
            upload_session=None,
        )
        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content.decode(), r"<td>\s*-+\s*</td>")

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    def test_in_progress_submission_expires_at(self) -> None:
        """Test that expiry date is shown for an in-progress submission with an upload session."""
        upload_session = UploadSession.new_session(user=cast(User, self.user))
        self._create_in_progress_submission(upload_session=upload_session)
        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        local_tz = ZoneInfo(settings.TIME_ZONE)
        expiry_date = upload_session.expires_at.astimezone(local_tz).strftime(
            "%a %b %d, %Y @ %H:%M"
        )
        # Strip leading zeroes from start of day and month
        expiry_date = re.sub(r"\s0+([^0]\d*)", r" \1", expiry_date)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        content = re.sub(r"\s+", " ", content).strip()
        self.assertIn(expiry_date, content)
        self.assertNotIn("red-text", content)
        self.assertNotIn("strikethrough", content)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    def test_in_progress_submission_expiring_soon(self) -> None:
        """Test that the expiry date is shown with a warning icon if the in-progress submission is expiring soon."""
        upload_session = UploadSession.new_session(user=cast(User, self.user))
        self._create_in_progress_submission(upload_session=upload_session)

        upload_session.last_upload_interaction_time = (
            upload_session.last_upload_interaction_time - timedelta(minutes=35)
        )
        upload_session.save()
        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Should show the warning icon for expiring soon
        self.assertIn("fa-exclamation-circle text-warning", content)
        self.assertIn("Submission is expiring soon", content)
        # Should NOT show the expired icon or text
        self.assertNotIn("fa-exclamation-triangle text-error", content)
        self.assertNotIn("Submission has expired", content)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    def test_in_progress_submission_expired(self) -> None:
        """Test that the expiry date is shown with the expired icon and tooltip if the in-progress
        submission has expired.
        """
        upload_session = UploadSession.new_session(user=cast(User, self.user))
        self._create_in_progress_submission(upload_session=upload_session)

        upload_session.last_upload_interaction_time = (
            upload_session.last_upload_interaction_time - timedelta(minutes=65)
        )
        upload_session.save()
        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Should show the expired icon and tooltip
        self.assertIn("fa-exclamation-triangle text-error", content)
        self.assertIn("Submission has expired", content)
        # Should NOT show the warning icon or text
        self.assertNotIn("fa-exclamation-circle text-warning", content)
        self.assertNotIn("Submission is expiring soon", content)

    @override_settings(PAGINATE_BY=3)
    def test_in_progress_submission_table_display(self) -> None:
        """Test that the in-progress submission table displays in-progress submissions
        correctly.
        """
        # Create in-progress submissions
        for i in range(3):
            self._create_in_progress_submission(title=f"Test In-Progress Submission {i}")

        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        for i in range(3):
            self.assertIn(f"Test In-Progress Submission {i}", response.content.decode())

    @override_settings(PAGINATE_BY=2)
    def test_in_progress_submission_table_pagination(self) -> None:
        """Test pagination for the in-progress submission table."""
        # Create in-progress submissions
        for i in range(3):
            self._create_in_progress_submission(title=f"Test In-Progress Submission {i}")

        # Test first page
        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test In-Progress Submission 0", response.content.decode())
        self.assertIn("Test In-Progress Submission 1", response.content.decode())
        self.assertNotIn("Test In-Progress Submission 2", response.content.decode())

        # Test second page
        response = self.client.get(
            f"{self.in_progress_table_url}?{PAGINATE_QUERY_NAME}=2",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test In-Progress Submission 2", response.content.decode())
        self.assertNotIn("Test In-Progress Submission 0", response.content.decode())
        self.assertNotIn("Test In-Progress Submission 1", response.content.decode())

    ### Tests for Submission Group Table ###

    def test_submission_group_table_empty(self) -> None:
        """Test that the submission group table works with no groups."""
        response = self.client.get(self.submission_group_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "includes/submission_group_table.html")
        content = response.content.decode()
        self.assertIn(_("You have not made any submission groups."), content)

    @override_settings(PAGINATE_BY=3)
    def test_submission_group_table_display(self) -> None:
        """Test that the submission group table displays submission groups correctly."""
        # Create submission groups
        for i in range(3):
            SubmissionGroup.objects.create(
                created_by=self.user,
                name=f"Test Group {i}",
                uuid=uuid.uuid4(),
            )

        response = self.client.get(self.submission_group_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        for i in range(3):
            self.assertIn(f"Test Group {i}", response.content.decode())

    @override_settings(PAGINATE_BY=2)
    def test_submission_group_table_pagination(self) -> None:
        """Test pagination for the submission group table."""
        # Create submission groups
        for i in range(3):
            SubmissionGroup.objects.create(
                created_by=self.user,
                name=f"Test Group {i}",
                uuid=uuid.uuid4(),
            )

        # Test first page
        response = self.client.get(self.submission_group_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Group 0", response.content.decode())
        self.assertIn("Test Group 1", response.content.decode())
        self.assertNotIn("Test Group 2", response.content.decode())

        # Test second page
        response = self.client.get(
            f"{self.submission_group_table_url}?{PAGINATE_QUERY_NAME}=2",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Group 2", response.content.decode())
        self.assertNotIn("Test Group 0", response.content.decode())
        self.assertNotIn("Test Group 1", response.content.decode())


class TestInProgressSubmission(TestCase):
    """Tests for the in_progress_submission view."""

    def setUp(self) -> None:
        """Set up the test case with users and in-progress submissions."""
        self.user = User.objects.create_user(
            username="testuser1", email="test@example.com", password="testpassword"
        )
        self.other_user = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpassword"
        )

        # Create upload sessions for each user
        self.upload_session = UploadSession.new_session(user=cast(User, self.user))
        self.other_upload_session = UploadSession.new_session(user=cast(User, self.other_user))

        # Create in-progress submissions for each user
        self.in_progress = InProgressSubmission.objects.create(
            user=self.user,
            upload_session=self.upload_session,
            current_step=SubmissionStep.CONTACT_INFO.value,
            title="Test Submission 1",
        )
        self.other_in_progress = InProgressSubmission.objects.create(
            user=self.other_user,
            upload_session=self.other_upload_session,
            current_step=SubmissionStep.CONTACT_INFO.value,
            title="Test Submission 2",
        )

        self.client.force_login(self.user)
        self.url = reverse(
            "recordtransfer:in_progress_submission", kwargs={"uuid": self.in_progress.uuid}
        )
        self.headers = {
            "HX-Request": "true",
        }

    # DELETE tests
    def test_delete_success(self) -> None:
        """Test successful deletion of an in-progress submission."""
        self.assertTrue(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

        response = self.client.delete(self.url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 204)

        # Check that HTMX showSuccess event is included in the response
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])

        # Check that deletion was successful
        self.assertFalse(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

    @patch("recordtransfer.views.profile.InProgressSubmission.delete")
    def test_delete_error(self, mock_delete: MagicMock) -> None:
        """Test that an error during deletion returns a 500 status code."""
        mock_delete.side_effect = Exception("Deletion error")

        response = self.client.delete(self.url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 500)

        # Check that HTMX showError event is included in the response
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

        # Check that the in-progress submission still exists
        self.assertTrue(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

    def test_non_htmx_delete_fails(self) -> None:
        """Test that a non-HTMX request fails with a 400 status code."""
        response = self.client.delete(self.url)

        # Check for proper status code
        self.assertEqual(response.status_code, 400)

        # Check that the in-progress submission still exists
        self.assertTrue(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

    def test_cannot_delete_other_users_submission(self) -> None:
        """Test that a user cannot delete another user's in-progress submission."""
        other_url = reverse(
            "recordtransfer:in_progress_submission", kwargs={"uuid": self.other_in_progress.uuid}
        )

        response = self.client.delete(other_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)

        # Verify the other user's submission still exists
        self.assertTrue(
            InProgressSubmission.objects.filter(uuid=self.other_in_progress.uuid).exists()
        )

    def test_login_required(self) -> None:
        """Test that login is required to access the view."""
        self.client.logout()

        response = self.client.get(self.url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(self.url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

        response = self.client.delete(self.url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

    def test_post_method_not_allowed(self) -> None:
        """Test that POST method is not allowed for this view."""
        response = self.client.post(self.url, headers=self.headers)
        self.assertEqual(response.status_code, 405)

    # GET tests (modal retrieval)
    def test_get_modal_success(self) -> None:
        """Test successful retrieval of the delete modal for an in-progress submission."""
        response = self.client.get(self.url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 200)

        # Check that the correct template is used
        self.assertTemplateUsed(response, "includes/delete_in_progress_submission_modal.html")

        # Check that the context contains the required variables
        self.assertEqual(response.context["in_progress"], self.in_progress)

        # Check that the in-progress submission's title is included in the response
        self.assertContains(response, "Test Submission 1")

    def test_non_htmx_get_fails(self) -> None:
        """Test that a non-HTMX request fails with a 400 status code."""
        response = self.client.get(self.url)

        # Check for proper status code
        self.assertEqual(response.status_code, 400)

    def test_cannot_get_other_users_submission_modal(self) -> None:
        """Test that a user cannot get the modal for another user's in-progress submission."""
        other_url = reverse(
            "recordtransfer:in_progress_submission", kwargs={"uuid": self.other_in_progress.uuid}
        )

        response = self.client.get(other_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_submission(self) -> None:
        """Test that requesting a modal for a nonexistent submission returns 404."""
        nonexistent_url = reverse(
            "recordtransfer:in_progress_submission", kwargs={"uuid": str(uuid.uuid4())}
        )

        response = self.client.get(nonexistent_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)
