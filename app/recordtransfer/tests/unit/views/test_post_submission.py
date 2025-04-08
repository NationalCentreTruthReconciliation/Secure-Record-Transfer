from unittest.mock import MagicMock, patch
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext

from recordtransfer.models import Submission, SubmissionGroup, User


class TestSubmissionGroupCreateView(TestCase):
    """Tests for SubmissionGroupCreateView."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.url = reverse("recordtransfer:submission_group_new")

    def setUp(self) -> None:
        """Set up test environment."""
        self.client.login(username="testuser", password="password")

    def test_access_authenticated_user(self) -> None:
        """Test that an authenticated user can access the view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_show_create.html")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_valid_form_submission(self) -> None:
        """Test that a valid form submission creates a new SubmissionGroup."""
        form_data = {
            "name": "Test Group",
            "description": "Test Description",
        }
        response = self.client.post(self.url, data=form_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), gettext("Group created"))
        self.assertTrue(SubmissionGroup.objects.filter(name="Test Group").exists())

    def test_invalid_form_submission(self) -> None:
        """Test that an invalid form submission does not create a new SubmissionGroup."""
        form_data = {
            "name": "",
            "description": "Test Description",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_show_create.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), gettext("There was an error creating the group"))

    def test_form_valid_json_response(self) -> None:
        """Test that a JsonResponse is returned when the form is valid and submitted from the
        submission form page.
        """
        form_data = {
            "name": "Test Group",
            "description": "Test Description",
        }
        response = self.client.post(self.url, data=form_data, HTTP_REFERER="submission/")
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["message"], gettext("Group created"))
        self.assertEqual(response_json["status"], "success")

    def test_form_invalid_json_response(self) -> None:
        """Test that a JsonResponse is returned when the form is invalid and submitted from the
        submission form page.
        """
        form_data = {
            "name": "",
            "description": "Test Description",
        }
        response = self.client.post(self.url, data=form_data, HTTP_REFERER="submission/")
        self.assertEqual(response.status_code, 400)
        response_json = response.json()
        self.assertEqual(response_json["message"], "This field is required.")
        self.assertEqual(response_json["status"], "error")


class TestSubmissionGroupDetailView(TestCase):
    """Tests for SubmissionGroupDetailView."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.staff_user = User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        cls.group = SubmissionGroup.objects.create(
            name="Test Group", description="Test Description", created_by=cls.user
        )
        cls.url = reverse(
            "recordtransfer:submission_group_detail", kwargs={"uuid": cls.group.uuid}
        )

    def setUp(self) -> None:
        """Set up test environment."""
        self.client.login(username="testuser", password="password")

    def test_access_authenticated_user(self) -> None:
        """Test that an authenticated user can access the view."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_show_create.html")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_access_non_creator_user(self) -> None:
        """Test that a non-creator user cannot access the view."""
        User.objects.create_user(username="noncreator", password="password")
        self.client.login(username="noncreator", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_access_staff_user(self) -> None:
        """Test that a staff user can access the view."""
        self.client.login(username="staffuser", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_show_create.html")

    def test_valid_form_submission(self) -> None:
        """Test that a valid form submission updates the SubmissionGroup."""
        form_data = {
            "name": "Updated Group",
            "description": "Updated Description",
        }
        response = self.client.post(self.url, data=form_data)
        # Check that the user is redirected back to the same page
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), gettext("Group updated"))
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Updated Group")
        self.assertEqual(self.group.description, "Updated Description")

    def test_invalid_form_submission(self) -> None:
        """Test that an invalid form submission does not update the SubmissionGroup."""
        form_data = {
            "name": "",
            "description": "Updated Description",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_show_create.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), gettext("There was an error updating the group"))
        self.group.refresh_from_db()
        self.assertNotEqual(self.group.description, "Updated Description")

    def test_get_context_data(self) -> None:
        """Test that the context data includes the submissions associated with the group."""
        submission = Submission.objects.create(user=self.user, part_of_group=self.group)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("submissions", response.context)
        self.assertIn(submission, response.context["submissions"])

    def test_delete_submission_group(self) -> None:
        """Test that the submission group can be deleted."""
        response = self.client.delete(self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), gettext("Group deleted"))
        self.assertRedirects(response, reverse("recordtransfer:user_profile"))
        self.assertFalse(SubmissionGroup.objects.filter(uuid=self.group.uuid).exists())

    def test_delete_other_user_submission_group(self) -> None:
        """Test that a user cannot delete another user's submission group."""
        other_user = User.objects.create_user(username="otheruser", password="password")
        other_group = SubmissionGroup.objects.create(
            name="Other Group", description="Other Description", created_by=other_user
        )
        url = reverse("recordtransfer:submission_group_detail", kwargs={"uuid": other_group.uuid})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    @patch("recordtransfer.views.post_submission.SubmissionGroup.delete")
    def test_delete_submission_group_error(self, mock_delete: MagicMock) -> None:
        """Test that an error during deletion is handled gracefully."""
        mock_delete.side_effect = Exception("Deletion error")
        response = self.client.delete(self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), gettext("There was an error deleting the group"))
        self.assertRedirects(response, reverse("recordtransfer:user_profile"))
