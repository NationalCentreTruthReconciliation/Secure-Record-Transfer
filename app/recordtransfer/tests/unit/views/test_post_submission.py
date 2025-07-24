from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from recordtransfer.models import Submission, SubmissionGroup, User


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
        cls.group_detail_url = reverse(
            "recordtransfer:submission_group_detail", kwargs={"uuid": cls.group.uuid}
        )

    def setUp(self) -> None:
        """Set up test environment."""
        self.client.login(username="testuser", password="password")

    def test_access_authenticated_user(self) -> None:
        """Test that an authenticated user can access the view."""
        response = self.client.get(self.group_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_detail.html")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.group_detail_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.group_detail_url}")

    def test_access_non_creator_user(self) -> None:
        """Test that a non-creator user cannot access the view."""
        User.objects.create_user(username="noncreator", password="password")
        self.client.login(username="noncreator", password="password")
        response = self.client.get(self.group_detail_url)
        self.assertEqual(response.status_code, 404)

    def test_access_staff_user(self) -> None:
        """Test that a staff user can access the view."""
        self.client.login(username="staffuser", password="password")
        response = self.client.get(self.group_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_detail.html")

    def test_valid_form_submission(self) -> None:
        """Test that a valid form submission updates the SubmissionGroup."""
        form_data = {
            "name": "Updated Group",
            "description": "Updated Description",
        }
        response = self.client.post(self.group_detail_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showSuccess", response.headers["HX-Trigger"])
        self.assertTemplateUsed(response, "recordtransfer/submission_group_detail.html")
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Updated Group")
        self.assertEqual(self.group.description, "Updated Description")

    def test_invalid_form_submission(self) -> None:
        """Test that an invalid form submission does not update the SubmissionGroup."""
        form_data = {
            "name": "",
            "description": "Updated Description",
        }
        response = self.client.post(self.group_detail_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_group_detail.html")
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("showError", response.headers["HX-Trigger"])
        self.group.refresh_from_db()
        self.assertNotEqual(self.group.description, "Updated Description")


class TestSubmissionDetailView(TestCase):
    """Tests for SubmissionDetailView."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.staff_user = User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        self.submission = Submission.objects.create(user=self.user)
        self.submission_detail_url = reverse(
            "recordtransfer:submission_detail", kwargs={"uuid": self.submission.uuid}
        )
        self.client.login(username="testuser", password="password")

    def test_access_authenticated_user(self) -> None:
        """Test that an authenticated user can access the view."""
        response = self.client.get(self.submission_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_detail.html")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.submission_detail_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.submission_detail_url}")

    def test_access_non_owner_user(self) -> None:
        """Test that a non-owner user cannot access the view."""
        User.objects.create_user(username="otheruser", password="password")
        self.client.login(username="otheruser", password="password")
        response = self.client.get(self.submission_detail_url)
        self.assertEqual(response.status_code, 404)

    def test_access_staff_user(self) -> None:
        """Test that a staff user can access the view."""
        self.client.login(username="staffuser", password="password")
        response = self.client.get(self.submission_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/submission_detail.html")

    def test_get_context_data(self) -> None:
        """Test that the context data includes required variables."""
        response = self.client.get(self.submission_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("submission", response.context)
        self.assertIn("current_date", response.context)
        self.assertIn("metadata", response.context)
        self.assertEqual(response.context["submission"], self.submission)

    def test_nonexistent_submission(self) -> None:
        """Test that accessing a nonexistent submission returns 404."""
        url = reverse(
            "recordtransfer:submission_detail",
            kwargs={"uuid": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestSubmissionCsvExport(TestCase):
    """Tests for the submission_csv_export view function."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.staff_user = User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        self.submission = Submission.objects.create(user=self.user)
        self.submission_csv_url = reverse(
            "recordtransfer:submission_csv", kwargs={"uuid": self.submission.uuid}
        )
        self.client.login(username="testuser", password="password")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.submission_csv_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.submission_csv_url}")

    def test_access_non_owner_user(self) -> None:
        """Test that a non-owner user cannot access the view."""
        User.objects.create_user(username="otheruser", password="password")
        self.client.login(username="otheruser", password="password")
        response = self.client.get(self.submission_csv_url)
        self.assertEqual(response.status_code, 404)

    @patch("recordtransfer.managers.SubmissionQuerySet.export_csv")
    def test_access_staff_user(self, mock_export: MagicMock) -> None:
        """Test that a staff user can access the view."""
        mock_export.return_value = HttpResponse("csv_content", content_type="text/csv")
        self.client.login(username="staffuser", password="password")
        response = self.client.get(self.submission_csv_url)
        self.assertEqual(response.status_code, 200)

    @patch("recordtransfer.managers.SubmissionQuerySet.export_csv")
    def test_csv_generation(self, mock_export: MagicMock) -> None:
        """Test that the CSV export is called with correct parameters."""
        mock_export.return_value = HttpResponse("csv_content", content_type="text/csv")
        response = self.client.get(self.submission_csv_url)
        self.assertEqual(response.status_code, 200)
        mock_export.assert_called_once()
        # Check that the export was called with the correct parameters
        call_args = mock_export.call_args
        self.assertIn("version", call_args.kwargs)
        self.assertIn("filename_prefix", call_args.kwargs)
        self.assertTrue(call_args.kwargs["filename_prefix"].startswith("testuser_export-"))

    def test_nonexistent_submission(self) -> None:
        """Test that accessing a nonexistent submission returns 404."""
        invalid_csv_url = reverse(
            "recordtransfer:submission_csv",
            kwargs={"uuid": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.get(invalid_csv_url)
        self.assertEqual(response.status_code, 404)


class TestSubmissionGroupBulkCsvExport(TestCase):
    """Tests for the submission_group_bulk_csv_export view function."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.staff_user = User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        self.submission_group = SubmissionGroup.objects.create(created_by=self.user)
        self.submission = Submission.objects.create(
            user=self.user, part_of_group=self.submission_group
        )
        self.submission_group_csv_url = reverse(
            "recordtransfer:submission_group_bulk_csv",
            kwargs={"uuid": self.submission_group.uuid},
        )
        self.client.login(username="testuser", password="password")

    def test_access_unauthenticated_user(self) -> None:
        """Test that an unauthenticated user is redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.submission_group_csv_url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.submission_group_csv_url}")

    def test_access_non_creator_user(self) -> None:
        """Test that a non-creator user cannot access the view."""
        User.objects.create_user(username="otheruser", password="password")
        self.client.login(username="otheruser", password="password")
        response = self.client.get(self.submission_group_csv_url)
        self.assertEqual(response.status_code, 404)

    @patch("recordtransfer.managers.SubmissionQuerySet.export_csv")
    def test_access_staff_user(self, mock_export: MagicMock) -> None:
        """Test that a staff user can access the view."""
        mock_export.return_value = HttpResponse("csv_content", content_type="text/csv")
        self.client.login(username="staffuser", password="password")
        response = self.client.get(self.submission_group_csv_url)
        self.assertEqual(response.status_code, 200)

    @patch("recordtransfer.managers.SubmissionQuerySet.export_csv")
    def test_invalid_group_uuid(self, mock_export: MagicMock) -> None:
        """Test that accessing a nonexistent submission group returns 404."""
        invalid_csv_url = reverse(
            "recordtransfer:submission_group_bulk_csv",
            kwargs={"uuid": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.get(invalid_csv_url)
        self.assertEqual(response.status_code, 404)

    @patch("recordtransfer.managers.SubmissionQuerySet.export_csv")
    def test_non_staff_user_owns_group_but_not_submissions(self, mock_export: MagicMock) -> None:
        """Test that a non-staff user cannot export CSV if they own the group but not the
        submissions.
        """
        user_one = User.objects.create_user(username="user_one", password="password")
        user_two = User.objects.create_user(username="user_two", password="password")
        user_one_group = SubmissionGroup.objects.create(
            name="Other User Group", created_by=user_one
        )

        Submission.objects.create(user=user_two, part_of_group=user_one_group)

        self.client.login(username="user_one", password="password")
        response = self.client.get(
            reverse(
                "recordtransfer:submission_group_bulk_csv", kwargs={"uuid": user_one_group.uuid}
            )
        )
        self.assertEqual(response.status_code, 404)


class TestGetUserSubmissionGroups(TestCase):
    """Tests for get_user_submission_groups view."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data for get_user_submission_groups view tests."""
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.other_user = User.objects.create_user(username="otheruser", password="password")
        cls.staff_user = User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        cls.group1 = SubmissionGroup.objects.create(name="Group 1", created_by=cls.user)
        cls.group2 = SubmissionGroup.objects.create(name="Group 2", created_by=cls.user)
        cls.other_group = SubmissionGroup.objects.create(
            name="Other Group", created_by=cls.other_user
        )
        cls.url = reverse("recordtransfer:get_user_submission_groups")

    def setUp(self) -> None:
        """Set up test environment for each test."""
        self.client.login(username="testuser", password="password")

    def test_returns_own_groups(self) -> None:
        """Test that the view returns only the groups owned by the user."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        group_names = {g["name"] for g in data}
        self.assertIn("Group 1", group_names)
        self.assertIn("Group 2", group_names)
        self.assertNotIn("Other Group", group_names)

    def test_returns_empty_for_user_with_no_groups(self) -> None:
        """Test that the view returns the correct response for a user with no groups."""
        self.client.login(username="otheruser", password="password")
        url = reverse("recordtransfer:get_user_submission_groups")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "uuid": str(self.other_group.uuid),
                    "name": "Other Group",
                    "description": self.other_group.description,
                }
            ],
        )

    def test_staff_can_access_own_groups(self) -> None:
        """Test that a staff user can access their own submission groups."""
        self.client.login(username="staffuser", password="password")
        url = reverse("recordtransfer:get_user_submission_groups")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Staff user has no groups by default
        self.assertEqual(response.json(), [])

    def test_group_descriptions_are_included_and_correct(self) -> None:
        """Test that the group descriptions are included and correct in the response."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Find the group by name and check description
        group1 = next((g for g in data if g["name"] == "Group 1"), None)
        group2 = next((g for g in data if g["name"] == "Group 2"), None)
        self.assertIsNotNone(group1)
        self.assertIsNotNone(group2)
        if group1 is not None:
            self.assertEqual(group1["description"], self.group1.description)

        if group2 is not None:
            self.assertEqual(group2["description"], self.group2.description)
