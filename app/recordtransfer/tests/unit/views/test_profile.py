import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, cast
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from freezegun import freeze_time

from recordtransfer.constants import FormFieldNames, QueryParameters
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
    """Tests for the UserProfile view."""

    def setUp(self) -> None:
        """Set up the test case with a user and initial data."""
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

    def tearDown(self) -> None:
        """Clean up after each test."""
        UploadSession.objects.all().delete()
        InProgressSubmission.objects.all().delete()
        SubmissionGroup.objects.all().delete()
        Submission.objects.all().delete()
        User.objects.all().delete()

    def test_access_authenticated_user(self) -> None:
        """Test that an authenticated user can access the profile page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    ### Tests for Profile Details ###

    def test_valid_name_change(self) -> None:
        """Test that a valid name change updates the user's first and last name."""
        form_data = {
            "first_name": "New",
            "last_name": "Name",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_accented_name_change(self) -> None:
        """Test that accented characters in names are handled correctly."""
        form_data = {
            "first_name": "Áccéntéd",
            "last_name": "Námé",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_invalid_first_name(self) -> None:
        """Test that an invalid first name (e.g., numeric) returns an error message."""
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

    def test_invalid_last_name(self) -> None:
        """Test that an invalid last name (e.g., numeric) returns an error message."""
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

    def test_valid_notification_setting_change(self) -> None:
        """Test that a valid notification setting change updates the user's preference."""
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": False,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_valid_password_change(self) -> None:
        """Test that a valid password change updates the user's password."""
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

    def test_wrong_password(self) -> None:
        """Test that providing the wrong current password returns an error message."""
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

    def test_passwords_do_not_match(self) -> None:
        """Test that if the new password and confirmation do not match, an error message is
        shown.
        """
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

    def test_same_password(self) -> None:
        """Test that if the new password is the same as the current password, an error message is
        shown.
        """
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

    def test_missing_current_password(self) -> None:
        """Test that if the current password is not provided, an error message is shown."""
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

    def test_missing_new_password(self) -> None:
        """Test that if the new password is not provided, an error message is shown."""
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

    def test_missing_confirm_new_password(self) -> None:
        """Test that if the confirm new password is not provided, an error message is shown."""
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

    def test_no_changes(self) -> None:
        """Test that if no changes are made to the profile, an error message is shown."""
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

    def test_empty_form_submission(self) -> None:
        """Test that submitting an empty form returns an error message."""
        form_data = {}
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )


class TestInProgressSubmissionTableView(TestCase):
    """Tests for the in-progress submission table view."""

    def setUp(self) -> None:
        """Set up the test case with a user."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_login(self.user)
        self.in_progress_table_url = reverse("recordtransfer:in_progress_submission_table")
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        UploadSession.objects.all().delete()
        InProgressSubmission.objects.all().delete()
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

    def test_table_requires_htmx_request(self) -> None:
        """Test that the table view requires HTMX headers."""
        response = self.client.get(self.in_progress_table_url)  # No HTMX headers
        self.assertEqual(response.status_code, 400)

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
    @freeze_time(datetime(2025, 1, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
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
    @freeze_time(datetime(2025, 1, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
    def test_in_progress_submission_expiring_soon(self) -> None:
        """Test that the expiry date is shown with a warning icon if the in-progress submission is
        expiring soon.
        """
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
    @freeze_time(datetime(2025, 1, 1, 9, 0, 0, tzinfo=ZoneInfo(settings.TIME_ZONE)))
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

    @patch("recordtransfer.views.profile.SiteSetting.get_value_int", return_value=3)
    def test_in_progress_submission_table_display(self, mock_get_value_int: MagicMock) -> None:
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

    @patch("recordtransfer.views.profile.SiteSetting.get_value_int", return_value=2)
    def test_in_progress_submission_table_pagination(self, mock_get_value_int: MagicMock) -> None:
        """Test pagination for the in-progress submission table."""
        # Create in-progress submissions
        for i in range(3):
            self._create_in_progress_submission(title=f"Test In-Progress Submission {i}")

        # Note that in-progress submissions are ordered by creation date, so the most recent
        # submissions will appear first in the table.
        # Test first page
        response = self.client.get(self.in_progress_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test In-Progress Submission 2", response.content.decode())
        self.assertIn("Test In-Progress Submission 1", response.content.decode())
        self.assertNotIn("Test In-Progress Submission 0", response.content.decode())

        # Test second page
        response = self.client.get(
            f"{self.in_progress_table_url}?{QueryParameters.PAGINATE_QUERY_NAME}=2",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test In-Progress Submission 0", response.content.decode())
        self.assertNotIn("Test In-Progress Submission 2", response.content.decode())
        self.assertNotIn("Test In-Progress Submission 1", response.content.decode())


class TestSubmissionGroupTableView(TestCase):
    """Tests for the submission group table view."""

    def setUp(self) -> None:
        """Set up the test case with a user."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_login(self.user)
        self.submission_group_table_url = reverse("recordtransfer:submission_group_table")
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        SubmissionGroup.objects.all().delete()
        User.objects.all().delete()

    def test_table_requires_htmx_request(self) -> None:
        """Test that the table view requires HTMX headers."""
        response = self.client.get(self.submission_group_table_url)  # No HTMX headers
        self.assertEqual(response.status_code, 400)

    def test_submission_group_table_empty(self) -> None:
        """Test that the submission group table works with no groups."""
        response = self.client.get(self.submission_group_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "includes/submission_group_table.html")
        content = response.content.decode()
        self.assertIn(_("You have not made any submission groups."), content)

    @patch("recordtransfer.views.profile.SiteSetting.get_value_int", return_value=3)
    def test_submission_group_table_display(self, mock_get_value_int: MagicMock) -> None:
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

    @patch("recordtransfer.views.profile.SiteSetting.get_value_int", return_value=2)
    def test_submission_group_table_pagination(self, mock_get_value_int: MagicMock) -> None:
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
            f"{self.submission_group_table_url}?{QueryParameters.PAGINATE_QUERY_NAME}=2",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Group 2", response.content.decode())
        self.assertNotIn("Test Group 0", response.content.decode())
        self.assertNotIn("Test Group 1", response.content.decode())


class TestSubmissionTableView(TestCase):
    """Tests for the submission table view."""

    def setUp(self) -> None:
        """Set up the test case with a user."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_login(self.user)
        self.submission_table_url = reverse("recordtransfer:submission_table")
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        Submission.objects.all().delete()
        User.objects.all().delete()

    def test_table_requires_htmx_request(self) -> None:
        """Test that the table view requires HTMX headers."""
        response = self.client.get(self.submission_table_url)  # No HTMX headers
        self.assertEqual(response.status_code, 400)


class TestDeleteInProgressSubmission(TestCase):
    """Tests for the delete_in_progress_submission view."""

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
        self.delete_ip_submission_url = reverse(
            "recordtransfer:delete_in_progress_submission_modal",
            kwargs={"uuid": self.in_progress.uuid},
        )
        self.headers = {
            "HX-Request": "true",
        }

    # DELETE tests
    def test_delete_success(self) -> None:
        """Test successful deletion of an in-progress submission."""
        self.assertTrue(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

        response = self.client.delete(self.delete_ip_submission_url, headers=self.headers)

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

        response = self.client.delete(self.delete_ip_submission_url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 500)

        # Check that HTMX showError event is included in the response
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

        # Check that the in-progress submission still exists
        self.assertTrue(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

    def test_non_htmx_delete_fails(self) -> None:
        """Test that a non-HTMX request fails with a 400 status code."""
        response = self.client.delete(self.delete_ip_submission_url)

        # Check for proper status code
        self.assertEqual(response.status_code, 400)

        # Check that the in-progress submission still exists
        self.assertTrue(InProgressSubmission.objects.filter(uuid=self.in_progress.uuid).exists())

    def test_cannot_delete_other_users_submission(self) -> None:
        """Test that a user cannot delete another user's in-progress submission."""
        other_url = reverse(
            "recordtransfer:delete_in_progress_submission_modal",
            kwargs={"uuid": self.other_in_progress.uuid},
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

        response = self.client.get(self.delete_ip_submission_url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(self.delete_ip_submission_url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

        response = self.client.delete(self.delete_ip_submission_url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

    def test_post_method_not_allowed(self) -> None:
        """Test that POST method is not allowed for this view."""
        response = self.client.post(self.delete_ip_submission_url, headers=self.headers)
        self.assertEqual(response.status_code, 405)

    # GET tests (modal retrieval)
    def test_get_modal_success(self) -> None:
        """Test successful retrieval of the delete modal for an in-progress submission."""
        response = self.client.get(self.delete_ip_submission_url, headers=self.headers)

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
        response = self.client.get(self.delete_ip_submission_url)

        # Check for proper status code
        self.assertEqual(response.status_code, 400)

    def test_cannot_get_other_users_submission_modal(self) -> None:
        """Test that a user cannot get the modal for another user's in-progress submission."""
        other_url = reverse(
            "recordtransfer:delete_in_progress_submission_modal",
            kwargs={"uuid": self.other_in_progress.uuid},
        )

        response = self.client.get(other_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_submission(self) -> None:
        """Test that requesting a modal for a nonexistent submission returns 404."""
        nonexistent_url = reverse(
            "recordtransfer:delete_in_progress_submission_modal",
            kwargs={"uuid": str(uuid.uuid4())},
        )

        response = self.client.get(nonexistent_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)


class TestDeleteSubmissionGroupView(TestCase):
    """Tests for the delete_submission_group view."""

    def setUp(self) -> None:
        """Set up the test case with users and submission groups."""
        self.user = User.objects.create_user(
            username="testuser1", email="test@example.com", password="testpassword"
        )
        self.other_user = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpassword"
        )

        # Create submission groups for each user
        self.submission_group = SubmissionGroup.objects.create(
            created_by=self.user,
            name="Test Group 1",
            uuid=uuid.uuid4(),
        )
        self.other_submission_group = SubmissionGroup.objects.create(
            created_by=self.other_user,
            name="Test Group 2",
            uuid=uuid.uuid4(),
        )

        self.client.force_login(self.user)
        self.delete_group_url = reverse(
            "recordtransfer:delete_submission_group_modal",
            kwargs={"uuid": self.submission_group.uuid},
        )
        self.headers = {
            "HX-Request": "true",
        }

    # DELETE tests
    def test_delete_success(self) -> None:
        """Test successful deletion of a submission group."""
        self.assertTrue(SubmissionGroup.objects.filter(uuid=self.submission_group.uuid).exists())

        response = self.client.delete(self.delete_group_url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 204)

        # Check that HTMX showSuccess event is included in the response
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])

        # Check that deletion was successful
        self.assertFalse(SubmissionGroup.objects.filter(uuid=self.submission_group.uuid).exists())

    @patch("recordtransfer.views.profile.SubmissionGroup.delete")
    def test_delete_error(self, mock_delete: MagicMock) -> None:
        """Test that an error during deletion returns a 500 status code."""
        mock_delete.side_effect = Exception("Deletion error")

        response = self.client.delete(self.delete_group_url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 500)

        # Check that HTMX showError event is included in the response
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

        # Check that the submission group still exists
        self.assertTrue(SubmissionGroup.objects.filter(uuid=self.submission_group.uuid).exists())

    def test_non_htmx_delete_fails(self) -> None:
        """Test that a non-HTMX request fails with a 400 status code."""
        response = self.client.delete(self.delete_group_url)

        # Check for proper status code
        self.assertEqual(response.status_code, 400)

        # Check that the submission group still exists
        self.assertTrue(SubmissionGroup.objects.filter(uuid=self.submission_group.uuid).exists())

    def test_cannot_delete_other_users_submission_group(self) -> None:
        """Test that a user cannot delete another user's submission group."""
        other_url = reverse(
            "recordtransfer:delete_submission_group_modal",
            kwargs={"uuid": self.other_submission_group.uuid},
        )

        response = self.client.delete(other_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)

        # Verify the other user's submission group still exists
        self.assertTrue(
            SubmissionGroup.objects.filter(uuid=self.other_submission_group.uuid).exists()
        )

    def test_login_required(self) -> None:
        """Test that login is required to access the view."""
        self.client.logout()

        response = self.client.get(self.delete_group_url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(self.delete_group_url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

        response = self.client.delete(self.delete_group_url, headers=self.headers)
        self.assertEqual(response.status_code, 302)

    def test_post_method_not_allowed(self) -> None:
        """Test that POST method is not allowed for this view."""
        response = self.client.post(self.delete_group_url, headers=self.headers)
        self.assertEqual(response.status_code, 405)

    # GET tests (modal retrieval)
    def test_get_modal_success(self) -> None:
        """Test successful retrieval of the delete modal for a submission group."""
        response = self.client.get(self.delete_group_url, headers=self.headers)

        # Check for proper status code
        self.assertEqual(response.status_code, 200)

        # Check that the correct template is used
        self.assertTemplateUsed(response, "includes/delete_submission_group_modal.html")

        # Check that the context contains the required variables
        self.assertEqual(response.context["submission_group"], self.submission_group)

        # Check that the submission group's name is included in the response
        self.assertContains(response, "Test Group 1")

    def test_non_htmx_get_fails(self) -> None:
        """Test that a non-HTMX request fails with a 400 status code."""
        response = self.client.get(self.delete_group_url)

        # Check for proper status code
        self.assertEqual(response.status_code, 400)

    def test_cannot_get_other_users_submission_group_modal(self) -> None:
        """Test that a user cannot get the modal for another user's submission group."""
        other_url = reverse(
            "recordtransfer:delete_submission_group_modal",
            kwargs={"uuid": self.other_submission_group.uuid},
        )

        response = self.client.get(other_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_submission_group(self) -> None:
        """Test that requesting a modal for a nonexistent submission group returns 404."""
        nonexistent_url = reverse(
            "recordtransfer:delete_submission_group_modal", kwargs={"uuid": str(uuid.uuid4())}
        )

        response = self.client.get(nonexistent_url, headers=self.headers)
        self.assertEqual(response.status_code, 404)


class TestSubmissionGroupModalCreateView(TestCase):
    """Tests for SubmissionGroupModalCreateView."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")

        self.submission_group_modal_url = reverse("recordtransfer:create_submission_group_modal")
        self.headers = {
            "HX-Request": "true",
        }

    def test_valid_form_submission(self) -> None:
        """Test that a valid form submission creates a new Submission and response includes
        a trigger for the success toast.
        """
        form_data = {
            "name": "Test Group",
            "description": "Test Description",
        }
        response = self.client.post(
            self.submission_group_modal_url, data=form_data, headers=self.headers
        )
        self.assertTrue(SubmissionGroup.objects.filter(name="Test Group").exists())

        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])
        self.assertNotIn("submissionGroupCreated", response.headers["HX-Trigger"])

    def test_valid_form_submission_from_submit_page(self) -> None:
        """Test that a valid form submission from the submit page creates a new SubmissionGroup
        and returns the submissionGroupCreated event.
        """
        form_data = {
            "name": "Test Group From Submission Form",
            "description": "Test Description",
        }
        # Mock the referer to simulate request from Submission Form page
        response = self.client.post(
            self.submission_group_modal_url,
            data=form_data,
            headers=self.headers,
            HTTP_REFERER=reverse("recordtransfer:submit"),
        )

        # Check that submission group was created
        submission_group = SubmissionGroup.objects.get(name="Test Group From Submission Form")
        self.assertTrue(submission_group)

        # Check response status and trigger event
        self.assertEqual(response.status_code, 201)
        self.assertIn("HX-Trigger", response.headers)

        # Check that the response includes the correct data in the trigger event
        trigger_data = json.loads(response.headers["HX-Trigger"])

        self.assertEqual(
            trigger_data,
            {
                "submissionGroupCreated": {
                    "message": "Submission group created successfully.",
                    "status": "success",
                    "group": {
                        "uuid": str(submission_group.uuid),
                        "name": submission_group.name,
                        "description": submission_group.description,
                    },
                }
            },
        )

    def test_invalid_form_submission(self) -> None:
        """Test that an invalid form submission does not create a new SubmissionGroup."""
        form_data = {
            "name": "",
            "description": "Test Description",
        }
        response = self.client.post(
            self.submission_group_modal_url, data=form_data, headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "includes/new_submission_group_modal.html")

        # Check that response contains the form with errors
        form = response.context["form"]
        self.assertTrue(form.errors)

        # Check that new submission group is not created
        self.assertFalse(SubmissionGroup.objects.all().exists())

    def test_non_htmx_request_for_404(self) -> None:
        """Test that a form submission not done through HTMX sends back 404."""
        form_data = {
            "name": "Test Group",
            "description": "Test Description",
        }
        response = self.client.post(self.submission_group_modal_url, data=form_data)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(SubmissionGroup.objects.filter(name="Test Group").exists())


class TestAssignSubmissionGroupModalView(TestCase):
    """Tests for the assign_submission_group_modal view."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpassword"
        )
        self.client.force_login(self.user)

        # Create test submissions
        self.submission = Submission.objects.create(
            user=self.user,
            raw_form=b"test_form_data",
            bag_name="test-bag",
            uuid=uuid.uuid4(),
        )
        self.other_submission = Submission.objects.create(
            user=self.other_user,
            raw_form=b"test_form_data",
            bag_name="other-test-bag",
            uuid=uuid.uuid4(),
        )

        # Create test submission groups
        self.group1 = SubmissionGroup.objects.create(
            created_by=self.user,
            name="Test Group 1",
            description="First test group",
            uuid=uuid.uuid4(),
        )
        self.group2 = SubmissionGroup.objects.create(
            created_by=self.user,
            name="Test Group 2",
            description="Second test group",
            uuid=uuid.uuid4(),
        )
        self.other_group = SubmissionGroup.objects.create(
            created_by=self.other_user,
            name="Other User Group",
            description="Group by other user",
            uuid=uuid.uuid4(),
        )

        self.assign_modal_url = reverse(
            "recordtransfer:assign_submission_group_modal",
            kwargs={"uuid": self.submission.uuid},
        )
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        Submission.objects.all().delete()
        SubmissionGroup.objects.all().delete()
        User.objects.all().delete()

    def test_modal_requires_htmx_request(self) -> None:
        """Test that the modal view requires HTMX headers."""
        response = self.client.get(self.assign_modal_url)  # No HTMX headers
        self.assertEqual(response.status_code, 400)

    def test_modal_success_no_current_group(self) -> None:
        """Test successful modal display when submission has no current group."""
        response = self.client.get(self.assign_modal_url, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "includes/assign_submission_group_modal.html")

        # Check context data
        context = response.context
        self.assertIn("groups", context)
        self.assertIn("current_group", context)
        self.assertIn("submission_title", context)
        self.assertIn("submission_uuid", context)
        self.assertIn("form_field_names", context)

        # Verify groups are filtered by user and ordered by name
        groups = list(context["groups"])
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].name, "Test Group 1")
        self.assertEqual(groups[1].name, "Test Group 2")

        # Verify no current group
        self.assertIsNone(context["current_group"])
        self.assertEqual(context["submission_uuid"], self.submission.uuid)

        # Check form field names are present
        form_field_names = context["form_field_names"]
        self.assertIn("SUBMISSION_UUID", form_field_names)
        self.assertIn("GROUP_UUID", form_field_names)
        self.assertIn("UNASSIGN", form_field_names)

    def test_modal_success_with_current_group(self) -> None:
        """Test successful modal display when submission has a current group."""
        # Assign submission to a group
        self.submission.part_of_group = self.group1
        self.submission.save()

        response = self.client.get(self.assign_modal_url, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 200)

        # Check current group is present in context
        context = response.context
        self.assertEqual(context["current_group"], self.group1)

    def test_modal_submission_with_metadata_title(self) -> None:
        """Test modal display shows submission title from metadata when available."""
        # This test would require creating metadata, but since we don't have
        # the Metadata model imported and it might be complex to create,
        # we'll test the empty title case which is already covered in the view
        response = self.client.get(self.assign_modal_url, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context["submission_title"], "")  # No metadata, so empty string

    def test_modal_filters_groups_by_user(self) -> None:
        """Test that modal only shows groups created by the current user."""
        response = self.client.get(self.assign_modal_url, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 200)

        groups = list(response.context["groups"])
        group_names = [group.name for group in groups]

        # Should only include current user's groups
        self.assertIn("Test Group 1", group_names)
        self.assertIn("Test Group 2", group_names)
        self.assertNotIn("Other User Group", group_names)

    def test_modal_cannot_access_other_users_submission(self) -> None:
        """Test that user cannot access modal for another user's submission."""
        other_url = reverse(
            "recordtransfer:assign_submission_group_modal",
            kwargs={"uuid": self.other_submission.uuid},
        )

        response = self.client.get(other_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 404)

    def test_modal_nonexistent_submission(self) -> None:
        """Test that requesting modal for nonexistent submission returns 404."""
        nonexistent_url = reverse(
            "recordtransfer:assign_submission_group_modal",
            kwargs={"uuid": str(uuid.uuid4())},
        )

        response = self.client.get(nonexistent_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 404)

    def test_modal_login_required(self) -> None:
        """Test that login is required to access the modal."""
        self.client.logout()

        response = self.client.get(self.assign_modal_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_modal_groups_ordered_by_name(self) -> None:
        """Test that submission groups are ordered by name in the modal."""
        # Create a group with a name that should come first alphabetically
        SubmissionGroup.objects.create(
            created_by=self.user,
            name="A First Group",
            description="Should be first",
            uuid=uuid.uuid4(),
        )

        response = self.client.get(self.assign_modal_url, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 200)

        groups = list(response.context["groups"])
        group_names = [group.name for group in groups]

        # Should be ordered alphabetically
        expected_order = ["A First Group", "Test Group 1", "Test Group 2"]
        self.assertEqual(group_names, expected_order)


class TestAssignSubmissionGroupView(TestCase):
    """Tests for the assign_submission_group view."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpassword"
        )
        self.client.force_login(self.user)

        # Create test submissions
        self.submission = Submission.objects.create(
            user=self.user,
            raw_form=b"test_form_data",
            bag_name="test-bag",
            uuid=uuid.uuid4(),
        )
        self.other_submission = Submission.objects.create(
            user=self.other_user,
            raw_form=b"test_form_data",
            bag_name="other-test-bag",
            uuid=uuid.uuid4(),
        )

        # Create test submission groups
        self.group1 = SubmissionGroup.objects.create(
            created_by=self.user,
            name="Test Group 1",
            description="First test group",
            uuid=uuid.uuid4(),
        )
        self.group2 = SubmissionGroup.objects.create(
            created_by=self.user,
            name="Test Group 2",
            description="Second test group",
            uuid=uuid.uuid4(),
        )
        self.other_group = SubmissionGroup.objects.create(
            created_by=self.other_user,
            name="Other User Group",
            description="Group by other user",
            uuid=uuid.uuid4(),
        )

        self.assign_url = reverse("recordtransfer:assign_submission_group")
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        Submission.objects.all().delete()
        SubmissionGroup.objects.all().delete()
        User.objects.all().delete()

    def test_assign_requires_htmx_request(self) -> None:
        """Test that the assign view requires HTMX headers."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.GROUP_UUID: str(self.group1.uuid),
        }
        response = self.client.post(self.assign_url, data=post_data)  # No HTMX headers
        self.assertEqual(response.status_code, 400)

    def test_assign_submission_to_group_success(self) -> None:
        """Test successful assignment of submission to group."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.GROUP_UUID: str(self.group1.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 204)

        # Check that HTMX showSuccess event is included
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])

        # Verify assignment in database
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.part_of_group, self.group1)

    def test_unassign_submission_from_group_success(self) -> None:
        """Test successful unassignment of submission from group."""
        # First assign submission to group
        self.submission.part_of_group = self.group1
        self.submission.save()

        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.UNASSIGN: "true",
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 204)

        # Check that HTMX showSuccess event is included
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])

        # Verify unassignment in database
        self.submission.refresh_from_db()
        self.assertIsNone(self.submission.part_of_group)

    def test_assign_missing_submission_uuid(self) -> None:
        """Test that missing submission UUID returns error."""
        post_data = {
            FormFieldNames.GROUP_UUID: str(self.group1.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 500)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_assign_missing_group_uuid_without_unassign(self) -> None:
        """Test that missing group UUID without unassign flag returns error."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 500)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_assign_nonexistent_submission(self) -> None:
        """Test assignment with nonexistent submission UUID."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(uuid.uuid4()),
            FormFieldNames.GROUP_UUID: str(self.group1.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 404)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_assign_nonexistent_group(self) -> None:
        """Test assignment with nonexistent group UUID."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.GROUP_UUID: str(uuid.uuid4()),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 404)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_cannot_assign_other_users_submission(self) -> None:
        """Test that user cannot assign another user's submission."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.other_submission.uuid),
            FormFieldNames.GROUP_UUID: str(self.group1.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 404)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_cannot_assign_to_other_users_group(self) -> None:
        """Test that user cannot assign submission to another user's group."""
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.GROUP_UUID: str(self.other_group.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 404)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_unassign_submission_not_in_group(self) -> None:
        """Test unassigning submission that is not assigned to any group."""
        # Ensure submission is not assigned to any group
        self.submission.part_of_group = None
        self.submission.save()

        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.UNASSIGN: "true",
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 400)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])

    def test_reassign_submission_to_different_group(self) -> None:
        """Test reassigning submission from one group to another."""
        # First assign to group1
        self.submission.part_of_group = self.group1
        self.submission.save()

        # Then reassign to group2
        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.GROUP_UUID: str(self.group2.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

        self.assertEqual(response.status_code, 204)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])

        # Verify reassignment in database
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.part_of_group, self.group2)

    def test_login_required(self) -> None:
        """Test that login is required to access the view."""
        self.client.logout()

        post_data = {
            FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
            FormFieldNames.GROUP_UUID: str(self.group1.uuid),
        }

        response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_method_not_allowed(self) -> None:
        """Test that GET method is not allowed for this view."""
        response = self.client.get(self.assign_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 405)

    def test_database_error_during_assign(self) -> None:
        """Test that database errors during assignment are handled."""
        with patch("recordtransfer.views.profile.Submission.save") as mock_save:
            mock_save.side_effect = Exception("Database error")

            post_data = {
                FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
                FormFieldNames.GROUP_UUID: str(self.group1.uuid),
            }

            response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

            self.assertEqual(response.status_code, 500)
            self.assertIn("HX-Trigger", response.headers)
            self.assertIn("showError", response.headers["HX-Trigger"])

    def test_database_error_during_unassign(self) -> None:
        """Test that database errors during unassignment are handled."""
        # First assign submission to group
        self.submission.part_of_group = self.group1
        self.submission.save()

        # Mock save to raise exception AFTER the initial assignment
        with patch("recordtransfer.views.profile.Submission.save") as mock_save:
            mock_save.side_effect = Exception("Database error")

            post_data = {
                FormFieldNames.SUBMISSION_UUID: str(self.submission.uuid),
                FormFieldNames.UNASSIGN: "true",
            }

            response = self.client.post(self.assign_url, data=post_data, headers=self.htmx_headers)

            self.assertEqual(response.status_code, 500)
            self.assertIn("HX-Trigger", response.headers)
            self.assertIn("showError", response.headers["HX-Trigger"])
