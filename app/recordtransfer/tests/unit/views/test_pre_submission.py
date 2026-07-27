import time
from typing import cast
from unittest.mock import MagicMock, PropertyMock, patch

from caais.models import RightsType, SourceRole, SourceType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from upload.handles import SESSION_KEY
from upload.models import UploadSession

from recordtransfer.constants import QueryParameters
from recordtransfer.enums import SubmissionStep
from recordtransfer.models import InProgressSubmission, SubmissionGroup, User
from recordtransfer.wizard_storage import LEGACY_WIZARD_DATA_VERSION, WIZARD_DATA_VERSION


def _set_handle(
    client: Client,
    handle: str,
    upload_session: UploadSession,
    ts: float | None = None,
) -> None:
    """Inject a handle -> upload_session mapping into the test client's session."""
    session = client.session
    handles = session.get(SESSION_KEY, {})
    handles[handle] = {"sid": upload_session.pk, "ts": ts if ts is not None else time.time()}
    session[SESSION_KEY] = handles
    session.save()


class OpenSessionsTests(TestCase):
    """Tests for the OpenSession view."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser1", email="user@example.com", password="zCNAD5&@Uy"
        )
        self.client.login(username="testuser1", password="zCNAD5&@Uy")

    def tearDown(self) -> None:
        """Tear down test data."""
        UploadSession.objects.filter(user=self.user).delete()

    @override_settings(UPLOAD_SESSION_MAX_CONCURRENT_OPEN=8)
    def test_no_sessions_in_context(self) -> None:
        """Test when the user has no open sessions."""
        response = self.client.get(reverse("recordtransfer:open_sessions"))
        self.assertContains(response, "You are Within the Session Limit")

    @override_settings(UPLOAD_SESSION_MAX_CONCURRENT_OPEN=8)
    def test_limit_almost_reached(self) -> None:
        """Test when the user has one fewer open session than the max."""
        for _ in range(7):
            UploadSession.new_session(user=self.user)

        response = self.client.get(reverse("recordtransfer:open_sessions"))
        self.assertContains(response, "You are Within the Session Limit")

    @override_settings(UPLOAD_SESSION_MAX_CONCURRENT_OPEN=8)
    def test_limit_reached(self) -> None:
        """Test when the user has reached the max."""
        for _ in range(8):
            UploadSession.new_session(user=self.user)

        response = self.client.get(reverse("recordtransfer:open_sessions"))
        self.assertContains(response, "Session Limit Reached")

    @override_settings(UPLOAD_SESSION_MAX_CONCURRENT_OPEN=-1)
    def test_no_limit(self) -> None:
        """Test when the user has reached the max default limit, but no limit is set."""
        for _ in range(8):
            UploadSession.new_session(user=self.user)

        response = self.client.get(reverse("recordtransfer:open_sessions"))
        self.assertContains(response, "You are Within the Session Limit")
        self.assertContains(
            response, "You are allowed to have as many concurrent sessions as you would like."
        )


class OpenSessionTableTests(TestCase):
    """Tests for the open_session_table view."""

    def setUp(self) -> None:
        """Set up the test case with a user."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_login(self.user)
        self.open_session_table_url = reverse("recordtransfer:open_session_table")
        self.htmx_headers = {
            "HX-Request": "true",
        }

    def tearDown(self) -> None:
        """Clean up after each test."""
        UploadSession.objects.all().delete()
        User.objects.all().delete()

    def test_table_requires_htmx_request(self) -> None:
        """Test that the table view requires HTMX headers."""
        response = self.client.get(self.open_session_table_url)  # No HTMX headers
        self.assertEqual(response.status_code, 400)

    def test_open_session_table_empty(self) -> None:
        """Test that the open session table works with no sessions."""
        response = self.client.get(self.open_session_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "includes/open_session_table.html")

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_display(self, mock_get_value_int: MagicMock) -> None:
        """Test that the open session table displays upload sessions correctly."""
        # Create upload sessions
        for _ in range(3):
            UploadSession.new_session(user=self.user)

        response = self.client.get(self.open_session_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)

        # Check that context data includes expected values
        context = response.context
        self.assertEqual(context["total_open_sessions"], 3)

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=2)
    def test_open_session_table_pagination(self, mock_get_value_int: MagicMock) -> None:
        """Test pagination for the open session table."""
        # Create upload sessions
        for _ in range(3):
            UploadSession.new_session(user=self.user)

        # Test first page
        response = self.client.get(self.open_session_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)

        # Should only show 2 sessions on first page (page size = 2)
        # Check that we got a valid response with sessions
        self.assertIn("page", response.context)
        page = response.context["page"]
        self.assertLessEqual(len(page.object_list), 2)

        # Test second page
        response = self.client.get(
            f"{self.open_session_table_url}?{QueryParameters.PAGINATE_QUERY_NAME}=2",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_sorting_functionality(self, mock_get_value_int: MagicMock) -> None:
        """Test that the open session table includes sorting functionality."""
        response = self.client.get(self.open_session_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)

        # Check that sorting controls and context are present
        context = response.context
        self.assertIn("sort_options", context)
        self.assertIn("Date Last Changed", context["sort_options"].values())
        self.assertIn("Date Started", context["sort_options"].values())
        self.assertIn("Files Uploaded", context["sort_options"].values())

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_default_sorting(self, mock_get_value_int: MagicMock) -> None:
        """Test that the open session table has default sorting applied."""
        response = self.client.get(self.open_session_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)

        # Check that default sort context is provided
        context = response.context
        self.assertEqual(context["current_sort"], "date_last_changed")
        self.assertEqual(context["current_direction"], "desc")

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_custom_sorting_by_date_started(
        self, mock_get_value_int: MagicMock
    ) -> None:
        """Test that custom sorting by date started works correctly."""
        # Test sorting by date started in ascending order
        response = self.client.get(
            f"{self.open_session_table_url}?sort=date_started&direction=asc",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["current_sort"], "date_started")
        self.assertEqual(context["current_direction"], "asc")

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_custom_sorting_by_upload_size_invalid(
        self, mock_get_value_int: MagicMock
    ) -> None:
        """Test that custom sorting by upload size falls back to default (not supported)."""
        # Note: upload_size sorting is not currently supported due to FileField limitations
        response = self.client.get(
            f"{self.open_session_table_url}?sort=upload_size&direction=desc",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)

        # Should fall back to default sorting when invalid sort is requested
        context = response.context
        self.assertEqual(context["current_sort"], "date_last_changed")
        self.assertEqual(context["current_direction"], "desc")

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_custom_sorting_by_file_count(
        self, mock_get_value_int: MagicMock
    ) -> None:
        """Test that custom sorting by file count works correctly."""
        # Test sorting by file count in ascending order
        response = self.client.get(
            f"{self.open_session_table_url}?sort=file_count&direction=asc",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["current_sort"], "file_count")
        self.assertEqual(context["current_direction"], "asc")

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    def test_open_session_table_invalid_params_fallback_to_defaults(
        self, mock_get_value_int: MagicMock
    ) -> None:
        """Invalid sort field and direction should fall back to defaults."""
        response = self.client.get(
            f"{self.open_session_table_url}?sort=invalid_field&direction=invalid_direction",
            headers=self.htmx_headers,
        )
        self.assertEqual(response.status_code, 200)

        context = response.context
        # Defaults for open session table
        self.assertEqual(context["current_sort"], "date_last_changed")
        self.assertEqual(context["current_direction"], "desc")

    @patch("recordtransfer.views.table.SiteSetting.get_value_int", return_value=3)
    @override_settings(UPLOAD_SESSION_MAX_CONCURRENT_OPEN=8)
    def test_open_session_table_context_data(self, mock_get_value_int: MagicMock) -> None:
        """Test that the open session table context includes expected data."""
        for _ in range(2):
            UploadSession.new_session(user=self.user)

        response = self.client.get(self.open_session_table_url, headers=self.htmx_headers)
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertIn("total_open_sessions", context)
        self.assertIn("max_open_sessions", context)
        self.assertEqual(context["total_open_sessions"], 2)
        self.assertEqual(context["max_open_sessions"], 8)


class SubmissionFormWizardTests(TestCase):
    """Tests for the SubmissionFormWizard view."""

    def setUp(self) -> None:
        """Set up the test case with a user and an in-progress submission."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser1", email="test@example.com", password="testpassword"
        )
        self.client.force_login(self.user)
        self.url = reverse("recordtransfer:submit")

        self.session = UploadSession.objects.create(
            token="1234567890abcdef",
            started_at=timezone.now(),
            user=self.user,
        )
        self.handle = "abcdabcd" * 4
        _set_handle(self.client, self.handle, self.session)

        self.test_data = [
            (SubmissionStep.ACCEPT_LEGAL.value, {"agreement_accepted": "on"}),
            (
                SubmissionStep.CONTACT_INFO.value,
                {
                    "contact_name": "John Doe",
                    "phone_number": "+1 (999) 999-9999",
                    "email": "john.doe@example.com",
                    "address_line_1": "123 Main St",
                    "city": "Winnipeg",
                    "province_or_state": "MB",
                    "postal_or_zip_code": "R3C 1A5",
                    "country": "CA",
                    "job_title": "Archivist",
                    "organization": "Test Organization",
                },
            ),
            (
                SubmissionStep.SOURCE_INFO.value,
                {
                    "enter_manual_source_info": "yes",
                    "source_name": "Test Source Name",
                    "source_type": SourceType.objects.filter(name="Individual").first().pk,
                    "source_role": SourceRole.objects.filter(name="Donor").first().pk,
                    "source_note": "Test Source Note",
                    "preliminary_custodial_history": "Test Custodial History",
                },
            ),
            (
                SubmissionStep.RECORD_DESCRIPTION.value,
                {
                    "accession_title": "Test Accession Title",
                    "date_of_materials": "2021-01-01 - 2021-12-31",
                    "language_of_material": "English",
                    "preliminary_scope_and_content": "Test Description",
                    "condition": "Test Condition",
                },
            ),
            (
                SubmissionStep.RIGHTS.value,
                [
                    {
                        "rights_type": RightsType.objects.filter(name="Copyright").first().pk,
                        "rights_value": "Test Note for Rights",
                    },
                ],
            ),
            (
                SubmissionStep.OTHER_IDENTIFIERS.value,
                [
                    {
                        "other_identifier_type": "Test Identifier Type",
                        "other_identifier_value": "Test Identifier Value",
                        "other_identifier_note": "Test Identifier Note",
                    },
                ],
            ),
            (
                SubmissionStep.GROUP_SUBMISSION.value,
                {
                    "group_uuid": SubmissionGroup.objects.create(
                        name="Test Group", created_by=self.user
                    ).uuid,
                },
            ),
            (
                SubmissionStep.UPLOAD_FILES.value,
                {
                    "general_note": "Test General Note",
                    "session_token": "1234567890abcdef",
                },
            ),
            (
                SubmissionStep.REVIEW.value,
                {},
            ),
        ]

    def tearDown(self) -> None:
        """Remove upload sessions and in-progress submissions."""
        UploadSession.objects.all().delete()
        InProgressSubmission.objects.all().delete()
        return super().tearDown()

    def _upload_test_file(self) -> None:
        """Upload a test file to the server using the provided upload handle."""
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("test_file.txt", b"contents", content_type="text/plain")},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(200, response.status_code)

    def _start_wizard(self) -> HttpResponse:
        """Create a draft through the launcher and load its canonical URL."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("?resume=", response.url)
        self.url = response.url
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        return response

    def _process_test_data(
        self, step: str, step_data: dict, response: HttpResponse | None = None
    ) -> dict:
        """Process the test data for the given step for form submission."""
        submit_data = {"submission_form_wizard-current_step": step}

        if step == SubmissionStep.UPLOAD_FILES.value:
            self._upload_test_file()

        if type(step_data) is dict:
            submit_data.update(
                {"{}-{}".format(step, key): value for key, value in step_data.items()}
            )
        elif type(step_data) is list:
            submit_data["{}-TOTAL_FORMS".format(step)] = str(len(step_data))
            submit_data["{}-INITIAL_FORMS".format(step)] = str(len(step_data))
            for i, item in enumerate(step_data):
                submit_data.update(
                    {"{}-{}-{}".format(step, i, key): value for key, value in item.items()}
                )

        return submit_data

    @override_settings(FILE_UPLOAD_ENABLED=True)
    @patch("recordtransfer.views.pre_submission.move_uploads_and_send_emails.delay")
    @patch("recordtransfer.views.pre_submission.UploadSession.new_session")
    def test_wizard(
        self,
        mock_session_create: MagicMock,
        mock_move_files: MagicMock,
    ) -> None:
        """Test the SubmissionFormWizard view from start to finish. This test will fill out the
        form with the test data and submit it, making sure no errors are raised.
        """
        mock_session_create.return_value = self.session
        mock_move_files.side_effect = RuntimeError("Redis unavailable")

        self._start_wizard()
        self.assertFalse(self.user.submission_set.exists())

        response = None

        for step, step_data in self.test_data:
            submit_data = self._process_test_data(step, step_data)

            if step == SubmissionStep.REVIEW.value:
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(self.url, submit_data, follow=True)
            else:
                response = self.client.post(self.url, submit_data, follow=True)
            self.assertEqual(200, response.status_code)

            if response.context and "form" in response.context:
                self.assertFalse(response.context["form"].errors)

        self.assertTrue(self.user.submission_set.exists())

        if response:
            self.assertEqual(200, response.status_code)
            # Check that response tells HTMX on client side to redirect to Submission Sent page
            hx_redirect = response.headers.get("HX-Redirect") or ""
            self.assertEqual(hx_redirect, reverse("recordtransfer:submission_sent"))
            # Follow the redirect to Submission Sent page
            response = self.client.get(hx_redirect, follow=True)
            self.assertEqual(200, response.status_code)

        mock_move_files.assert_called_once()
        submission = self.user.submission_set.get()
        self.assertEqual(submission.upload_session, self.session)
        self.assertTrue(UploadSession.objects.filter(pk=self.session.pk).exists())
        self.assertFalse(self.user.inprogresssubmission_set.exists())

    @override_settings(FILE_UPLOAD_ENABLED=True)
    def test_existing_draft_session_prevents_duplicate_session_creation(self) -> None:
        """A stale transition reuses the relation instead of creating another session."""
        self._start_wizard()
        draft = self.user.inprogresssubmission_set.get()
        draft.current_step = SubmissionStep.GROUP_SUBMISSION.value
        draft.upload_session = self.session
        draft.step_data["wizard"]["step"] = SubmissionStep.GROUP_SUBMISSION.value
        draft.save(update_fields=["current_step", "upload_session", "step_data"])
        submit_data = {
            "submission_form_wizard-current_step": SubmissionStep.GROUP_SUBMISSION.value,
        }

        with patch("recordtransfer.views.pre_submission.UploadSession.new_session") as new_session:
            response = self.client.post(self.url, submit_data)

        self.assertEqual(response.status_code, 200)
        new_session.assert_not_called()
        draft.refresh_from_db()
        self.assertEqual(draft.upload_session, self.session)
        self.assertEqual(draft.current_step, SubmissionStep.UPLOAD_FILES.value)
        self.assertEqual(draft.step_data["wizard"]["extra_data"]["session_token"], self.session.token)

    @override_settings(FILE_UPLOAD_ENABLED=True)
    def test_finalization_failure_rolls_back_and_leaves_draft_resumable(self) -> None:
        """A metadata failure preserves the draft and its upload session."""
        self._start_wizard()

        with patch(
            "recordtransfer.views.pre_submission.UploadSession.new_session",
            return_value=self.session,
        ):
            for step, step_data in self.test_data[:-1]:
                response = self.client.post(self.url, self._process_test_data(step, step_data))
                self.assertEqual(response.status_code, 200)

        draft = self.user.inprogresssubmission_set.get()
        self.assertEqual(draft.upload_session, self.session)

        with (
            patch.object(
                InProgressSubmission,
                "delete",
                side_effect=RuntimeError("draft deletion failed"),
            ),
            patch("recordtransfer.views.pre_submission.move_uploads_and_send_emails.delay") as move,
            patch("recordtransfer.views.pre_submission.send_submission_creation_failure.delay"),
            patch(
                "recordtransfer.views.pre_submission.send_your_submission_did_not_go_through.delay"
            ),
            self.assertRaisesMessage(Exception, "There was an error creating your submission"),
        ):
            self.client.post(
                self.url,
                self._process_test_data(*self.test_data[-1]),
            )

        draft.refresh_from_db()
        self.assertEqual(draft.upload_session, self.session)
        self.assertTrue(UploadSession.objects.filter(pk=self.session.pk).exists())
        self.assertFalse(self.user.submission_set.exists())
        move.assert_not_called()

    @override_settings(FILE_UPLOAD_ENABLED=True, UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES=60)
    def test_saving_expirable_in_progress_submission(self) -> None:
        """Test that saving an expirable in-progress submission. Saves the form on the
        Upload Files step after uploading a file.
        """
        self._start_wizard()
        self.assertEqual(self.user.inprogresssubmission_set.count(), 1)

        for step, step_data in self.test_data:
            submit_data = self._process_test_data(step, step_data)

            if step == SubmissionStep.UPLOAD_FILES.value:
                submit_data["save_form_step"] = step
                response = self.client.post(self.url, submit_data, follow=True)
                self.assertEqual(200, response.status_code)
                # Check that response tells HTMX on client side to redirect to user profile
                hx_redirect = response.headers.get("HX-Redirect") or ""
                self.assertEqual(hx_redirect, reverse("recordtransfer:user_profile"))
                # Follow the redirect to user profile
                response = self.client.get(hx_redirect, follow=True)
                self.assertEqual(200, response.status_code)
                self.assertContains(
                    response, "Submission saved successfully. This submission will expire on"
                )
                self.assertTrue(self.user.inprogresssubmission_set.exists())
                self.assertFalse(self.user.inprogresssubmission_set.first().upload_session_expired)
                break

            else:
                response = self.client.post(self.url, submit_data, follow=True)
                self.assertEqual(200, response.status_code)

    @override_settings(UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES=60)
    def test_saving_unexpirable_in_progress_submission(self) -> None:
        """Test saving an unexpirable in-progress submission. Saves the form on the Rights step
        after filling out the form.
        """
        self._start_wizard()
        self.assertEqual(self.user.inprogresssubmission_set.count(), 1)

        for step, step_data in self.test_data:
            submit_data = self._process_test_data(step, step_data)

            if step == SubmissionStep.RIGHTS.value:
                submit_data["save_form_step"] = step
                response = self.client.post(self.url, submit_data, follow=True)
                self.assertEqual(200, response.status_code)
                # Check that response tells HTMX on client side to redirect to user profile
                hx_redirect = response.headers.get("HX-Redirect") or ""
                self.assertEqual(hx_redirect, reverse("recordtransfer:user_profile"))
                # Follow the redirect to user profile
                response = self.client.get(hx_redirect, follow=True)
                self.assertEqual(200, response.status_code)
                self.assertContains(response, "Submission saved successfully.")
                self.assertNotContains(response, "This submission will expire on")
                self.assertTrue(self.user.inprogresssubmission_set.exists())
                self.assertFalse(self.user.inprogresssubmission_set.first().upload_session_expired)
                self.assertEqual(
                    self.user.inprogresssubmission_set.first().step_data["version"],
                    WIZARD_DATA_VERSION,
                )
                break

            else:
                response = self.client.post(self.url, submit_data, follow=True)
                self.assertEqual(200, response.status_code)

    @patch(
        "recordtransfer.models.InProgressSubmission.upload_session_expired",
        new_callable=PropertyMock,
    )
    def test_resume_expired_in_progress_submission(self, mock_expired: PropertyMock) -> None:
        """Test that the view redirects to the submission expired page if the in-progress
        submission is expired.
        """
        upload_session = UploadSession.new_session(user=cast(User, self.user))
        in_progress = InProgressSubmission.objects.create(
            user=self.user,
            upload_session=upload_session,
            current_step=SubmissionStep.CONTACT_INFO.value,
        )
        mock_expired.return_value = True
        response = self.client.get(self.url, {"resume": in_progress.uuid}, follow=True)
        self.assertRedirects(response, reverse("recordtransfer:in_progress_submission_expired"))

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        UPLOAD_SESSION_MAX_CONCURRENT_OPEN=4,
    )
    def test_session_limit_reached_get(self) -> None:
        """Test that the user is redirected to the session limit page with a GET request."""
        while self.user.open_upload_sessions().count() < 4:
            UploadSession.new_session(user=self.user)

        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("recordtransfer:open_sessions"))

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        UPLOAD_SESSION_MAX_CONCURRENT_OPEN=4,
    )
    def test_session_limit_reached_mid_form(self) -> None:
        """Test that the session limit is reached during a POST request, i.e., mid-form."""
        self._start_wizard()

        self.assertEqual(1, self.user.inprogresssubmission_set.count())  # type: ignore

        response = None

        for step, step_data in self.test_data:
            submit_data = self._process_test_data(step, step_data)

            # Create sessions so that count is one over the limit
            if step == SubmissionStep.RECORD_DESCRIPTION.value:
                while self.user.open_sessions_within_limit():
                    UploadSession.new_session(user=self.user)

            response = self.client.post(self.url, submit_data, follow=True)

            if step == SubmissionStep.RECORD_DESCRIPTION.value:
                hx_redirect = response.headers.get("HX-Redirect") or ""
                self.assertEqual(hx_redirect, reverse("recordtransfer:open_sessions"))

                # Follow the redirect
                redirected_response = self.client.get(hx_redirect, follow=True)
                self.assertEqual(200, redirected_response.status_code)

                self.assertContains(
                    redirected_response,
                    "Your submission was saved, but you have reached your session limit.",
                )

                # There should now be a saved submission
                self.assertEqual(1, self.user.inprogresssubmission_set.count())  # type: ignore
                break

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        UPLOAD_SESSION_MAX_CONCURRENT_OPEN=4,
    )
    def test_resume_submission_without_session_at_max(self) -> None:
        """Test that resuming a submission without a session when the user has the max sessions
        already redirects to the open sessions page.
        """
        # Create sessions up to the max
        while self.user.open_upload_sessions().count() < 4:
            UploadSession.new_session(user=self.user)

        # Create an in-progress submission *without* a session linked
        in_progress = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.RECORD_DESCRIPTION.value,
            step_data={
                "version": LEGACY_WIZARD_DATA_VERSION,
                "past": {},
                "current": {},
                "extra": {},
            },
        )

        response = self.client.get(self.url, {"resume": in_progress.uuid}, follow=True)
        self.assertRedirects(response, reverse("recordtransfer:open_sessions"))

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        UPLOAD_SESSION_MAX_CONCURRENT_OPEN=4,
    )
    def test_resume_submission_with_session_at_max(self) -> None:
        """Test that resuming a submission with a session when the user has the max sessions allows
        a user to continue with the form.
        """
        # Create up to the max MINUS one
        while self.user.open_upload_sessions().count() < 3:
            UploadSession.new_session(user=self.user)

        # And create one more to take it to the max, except this one will be linked to the
        # in-progress submission
        session = UploadSession.new_session(user=self.user)

        # Create an in-progress submission *without* a session linked
        in_progress = InProgressSubmission.objects.create(
            user=self.user,
            current_step=SubmissionStep.RECORD_DESCRIPTION.value,
            upload_session=session,
            step_data={
                "version": LEGACY_WIZARD_DATA_VERSION,
                "past": {},
                "current": {},
                "extra": {
                    "session_token": session.token,
                },
            },
        )

        response = self.client.get(self.url, {"resume": in_progress.uuid}, follow=True)

        self.assertEqual(200, response.status_code)
        # Assert that we're on the proper page
        self.assertContains(response, "Record Description")

    def test_launcher_creates_canonical_versioned_draft(self) -> None:
        """A bare GET creates one versioned draft and redirects to its UUID URL."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        draft = InProgressSubmission.objects.get(user=self.user)
        self.assertEqual(response.url, draft.get_resume_url())
        self.assertEqual(draft.step_data["version"], WIZARD_DATA_VERSION)

    def test_parallel_launches_create_distinct_drafts(self) -> None:
        """Each bare GET receives an independent persisted wizard identity."""
        first_response = self.client.get(self.url)
        second_response = self.client.get(self.url)

        self.assertNotEqual(first_response.url, second_response.url)
        self.assertEqual(InProgressSubmission.objects.filter(user=self.user).count(), 2)

    def test_canonical_get_does_not_reset_persisted_step(self) -> None:
        """Refreshing a canonical wizard URL retains its data and current step."""
        self._start_wizard()
        submit_data = self._process_test_data(*self.test_data[0])
        response = self.client.post(self.url, submit_data)
        self.assertEqual(response.status_code, 200)

        draft = InProgressSubmission.objects.get(user=self.user)
        self.assertEqual(draft.current_step, SubmissionStep.CONTACT_INFO.value)
        self.assertIn(SubmissionStep.ACCEPT_LEGAL.value, draft.step_data["wizard"]["step_data"])

        response = self.client.get(self.url)
        self.assertContains(response, "Contact Information")
        draft.refresh_from_db()
        self.assertEqual(draft.current_step, SubmissionStep.CONTACT_INFO.value)

    def test_actions_in_one_draft_do_not_change_another(self) -> None:
        """Separate canonical wizard URLs persist independent state."""
        first_url = self.client.get(self.url).url
        second_url = self.client.get(self.url).url
        submit_data = self._process_test_data(*self.test_data[0])

        response = self.client.post(first_url, submit_data)
        self.assertEqual(response.status_code, 200)

        first_uuid = first_url.rsplit("=", maxsplit=1)[-1]
        second_uuid = second_url.rsplit("=", maxsplit=1)[-1]
        first_draft = InProgressSubmission.objects.get(uuid=first_uuid)
        second_draft = InProgressSubmission.objects.get(uuid=second_uuid)
        self.assertEqual(first_draft.current_step, SubmissionStep.CONTACT_INFO.value)
        self.assertEqual(second_draft.current_step, SubmissionStep.ACCEPT_LEGAL.value)
        self.assertEqual(second_draft.step_data["wizard"]["step_data"], {})

    def test_bare_post_returns_not_found(self) -> None:
        """A POST without a draft identity cannot discard data through canonicalization."""
        response = self.client.post(self.url, self._process_test_data(*self.test_data[0]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(InProgressSubmission.objects.filter(user=self.user).exists())

    def test_explicit_save_preserves_invalid_current_step(self) -> None:
        """Save stores unvalidated current fields canonically and restores them on resume."""
        self._start_wizard()
        response = self.client.post(self.url, self._process_test_data(*self.test_data[0]))
        self.assertEqual(response.status_code, 200)
        submit_data = {
            "submission_form_wizard-current_step": SubmissionStep.CONTACT_INFO.value,
            "contactinfo-contact_name": "Partial Donor",
            "save_form_step": SubmissionStep.CONTACT_INFO.value,
        }

        response = self.client.post(self.url, submit_data)

        self.assertEqual(response.headers["HX-Redirect"], reverse("recordtransfer:user_profile"))
        draft = InProgressSubmission.objects.get(user=self.user)
        self.assertEqual(draft.step_data["version"], WIZARD_DATA_VERSION)
        saved_contact = draft.step_data["wizard"]["step_data"][SubmissionStep.CONTACT_INFO.value]
        self.assertEqual(saved_contact["contactinfo-contact_name"], ["Partial Donor"])

        response = self.client.get(self.url)
        self.assertContains(response, 'value="Partial Donor"')

    def test_explicit_save_preserves_formset_management_data(self) -> None:
        """Save retains formset rows and management fields in formtools' raw representation."""
        self._start_wizard()
        draft = InProgressSubmission.objects.get(user=self.user)
        draft.current_step = SubmissionStep.RIGHTS.value
        draft.step_data["wizard"]["step"] = SubmissionStep.RIGHTS.value
        draft.save(update_fields=["current_step", "step_data"])
        rights_type = RightsType.objects.get(name="Copyright")
        submit_data = {
            "submission_form_wizard-current_step": SubmissionStep.RIGHTS.value,
            "rights-TOTAL_FORMS": "1",
            "rights-INITIAL_FORMS": "0",
            "rights-0-rights_type": str(rights_type.pk),
            "rights-0-rights_value": "Saved restriction",
            "save_form_step": SubmissionStep.RIGHTS.value,
        }

        response = self.client.post(self.url, submit_data)

        self.assertEqual(response.headers["HX-Redirect"], reverse("recordtransfer:user_profile"))
        draft.refresh_from_db()
        saved_rights = draft.step_data["wizard"]["step_data"][SubmissionStep.RIGHTS.value]
        self.assertEqual(saved_rights["rights-TOTAL_FORMS"], ["1"])
        self.assertEqual(saved_rights["rights-0-rights_value"], ["Saved restriction"])

        response = self.client.get(self.url)
        self.assertContains(response, "Saved restriction")

    def test_unknown_draft_returns_not_found(self) -> None:
        """An unknown canonical UUID does not silently create a replacement draft."""
        response = self.client.get(self.url, {"resume": "00000000-0000-0000-0000-000000000000"})

        self.assertEqual(response.status_code, 404)
        self.assertFalse(InProgressSubmission.objects.filter(user=self.user).exists())
