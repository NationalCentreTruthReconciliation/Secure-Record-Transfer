from typing import cast
from unittest.mock import MagicMock, PropertyMock, patch

from caais.models import RightsType, SourceRole, SourceType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from recordtransfer.enums import SubmissionStep
from recordtransfer.models import InProgressSubmission, SubmissionGroup, UploadSession, User


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

    def _upload_test_file(self) -> None:
        """Upload a test file to the server using the provided session token."""
        response = self.client.post(
            reverse("recordtransfer:upload_files", kwargs={"session_token": "1234567890abcdef"}),
            {"file": SimpleUploadedFile("test_file.txt", b"contents", content_type="text/plain")},
        )
        self.assertEqual(200, response.status_code)

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
    @patch("recordtransfer.views.pre_submission.send_submission_creation_success.delay")
    @patch("recordtransfer.views.pre_submission.send_thank_you_for_your_submission.delay")
    @patch("recordtransfer.views.pre_submission.UploadSession.new_session")
    def test_wizard(
        self,
        mock_session_create: MagicMock,
        mock_thank_you: MagicMock,
        mock_creation_success: MagicMock,
    ) -> None:
        """Test the SubmissionFormWizard view from start to finish. This test will fill out the
        form with the test data and submit it, making sure no errors are raised.
        """
        mock_session_create.return_value = self.session
        mock_thank_you.return_value = None
        mock_creation_success.return_value = None

        self.assertEqual(200, self.client.get(self.url).status_code)
        self.assertFalse(self.user.submission_set.exists())

        response = None

        for step, step_data in self.test_data:
            submit_data = self._process_test_data(step, step_data)

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

    @override_settings(FILE_UPLOAD_ENABLED=True, UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES=60)
    def test_saving_expirable_in_progress_submission(self) -> None:
        """Test that saving an expirable in-progress submission. Saves the form on the
        Upload Files step after uploading a file.
        """
        self.assertEqual(200, self.client.get(self.url).status_code)
        # Check that the in-progress submission does not exist yet
        self.assertFalse(self.user.inprogresssubmission_set.exists())

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
        self.assertEqual(200, self.client.get(self.url).status_code)
        # Check that the in-progress submission does not exist yet
        self.assertFalse(self.user.inprogresssubmission_set.exists())

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
