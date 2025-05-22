from typing import cast
from unittest.mock import MagicMock, PropertyMock, patch

from caais.models import RightsType, SourceRole, SourceType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

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
                },
            ),
            (
                SubmissionStep.REVIEW.value,
                {},
            ),
        ]

    def _upload_test_file(self) -> str:
        """Upload a test file to the server. Returns the upload session token used to upload the
        file.
        """
        response = self.client.post(reverse("recordtransfer:create_upload_session"))
        self.assertEqual(201, response.status_code)
        session_token = response.json()["uploadSessionToken"]

        test_file = SimpleUploadedFile("test_file.txt", b"file_content", content_type="text/plain")
        response = self.client.post(
            reverse("recordtransfer:upload_files", kwargs={"session_token": session_token}),
            {"file": test_file},
        )
        self.assertEqual(200, response.status_code)

        return session_token

    def _process_test_data(self, step: str, step_data: dict) -> dict:
        """Process the test data for the given step for form submission."""
        submit_data = {"submission_form_wizard-current_step": step}

        if step == SubmissionStep.UPLOAD_FILES.value:
            session_token = self._upload_test_file()
            submit_data[f"{step}-session_token"] = session_token

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

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", True)
    @patch("django_recaptcha.fields.ReCaptchaField.clean")
    @patch("recordtransfer.views.pre_submission.send_submission_creation_success.delay")
    @patch("recordtransfer.views.pre_submission.send_thank_you_for_your_submission.delay")
    def test_wizard(
        self, mock_thank_you: MagicMock, mock_creation_success: MagicMock, mock_clean: MagicMock
    ) -> None:
        """Test the SubmissionFormWizard view from start to finish. This test will fill out the form
        with the test data and submit it, making sure no errors are raised.
        """
        mock_thank_you.return_value = None
        mock_creation_success.return_value = None
        mock_clean.return_value = "PASSED"
        self.assertEqual(200, self.client.get(self.url).status_code)
        self.assertFalse(self.user.submission_set.exists())
        response = None
        for step, step_data in self.test_data:
            submit_data = self._process_test_data(step, step_data)

            response = self.client.post(self.url, submit_data, follow=True)
            self.assertEqual(200, response.status_code)

            if "form" in response.context:
                self.assertFalse(response.context["form"].errors)
        self.assertTrue(self.user.submission_set.exists())
        if response:
            self.assertRedirects(response, reverse("recordtransfer:submission_sent"))

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", True)
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

    @patch("django.conf.settings.UPLOAD_SESSION_EXPIRE_AFTER_INACTIVE_MINUTES", 60)
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
