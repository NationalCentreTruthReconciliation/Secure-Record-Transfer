import re
from datetime import datetime, timedelta
from typing import cast
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from recordtransfer.models import InProgressSubmission, UploadSession, User


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

        # Submission history related
        self.upload_session = UploadSession.new_session(user=cast(User, self.user))
        self.in_progress_submission = InProgressSubmission.objects.create(
            user=self.user,
            uuid="550e8400-e29b-41d4-a716-446655440000",
            upload_session=self.upload_session,
        )

    def test_access_authenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")

    def test_access_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

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

    # Testing submission expiry
    def test_in_progress_submission_expires_at_no_expiry(self) -> None:
        """Test that the "Expires at" cell contains just a dash when the in-progress submission
        has no upload session, hence no expiry date.
        """
        self.in_progress_submission.upload_session = None
        self.in_progress_submission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.content.decode(), r"<td>\s*-+\s*</td>")

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    def test_in_progress_submission_expires_at(self) -> None:
        """Test that expiry date is shown for an in-progress submission with an upload session."""
        response = self.client.get(self.url)
        local_tz = ZoneInfo(settings.TIME_ZONE)
        expiry_date = self.upload_session.expires_at.astimezone(local_tz).strftime(
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
    def test_in_progress_submission_expiring_soon_shown_in_red(self) -> None:
        """Test that the expiry date is shown in red if the in-progress submission is expiring
        soon.
        """
        self.upload_session.last_upload_interaction_time = (
            self.upload_session.last_upload_interaction_time - timedelta(minutes=35)
        )
        self.upload_session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("red-text", content)
        self.assertNotIn("strikethrough", content)

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRING_REMINDER_MINUTES", 30)
    def test_in_progress_submission_expired(self) -> None:
        """Test that the expiry date is shown in red and strikethrough if the in-progress submission
        has expired.
        """
        self.upload_session.last_upload_interaction_time = (
            self.upload_session.last_upload_interaction_time - timedelta(minutes=65)
        )
        self.upload_session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("red-text", content)
        self.assertIn("strikethrough", content)
