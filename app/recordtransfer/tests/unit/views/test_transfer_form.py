from caais.models import RightsType, SourceRole, SourceType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from recordtransfer.enums import TransferStep
from recordtransfer.models import SubmissionGroup, User


class TransferFormWizardTests(TestCase):
    """Tests for the TransferFormWizard view."""

    def setUp(self) -> None:
        """Set up the test case with a user and an in-progress submission."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser1", email="test@example.com", password="testpassword"
        )
        self.client.force_login(self.user)
        self.url = reverse("recordtransfer:transfer")

    def test_wizard_view(self) -> None:
        """Test that the form is rendered correctly."""
        data = [
            (TransferStep.ACCEPT_LEGAL.value, {"agreement_accepted": "on"}),
            (
                TransferStep.CONTACT_INFO.value,
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
                TransferStep.SOURCE_INFO.value,
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
                TransferStep.RECORD_DESCRIPTION.value,
                {
                    "accession_title": "Test Accession Title",
                    "date_of_materials": "2021-01-01 - 2021-12-31",
                    "language_of_material": "English",
                    "preliminary_scope_and_content": "Test Description",
                    "condition": "Test Condition",
                },
            ),
            (
                TransferStep.RIGHTS.value,
                [
                    {
                        "rights_type": RightsType.objects.filter(name="Copyright").first().pk,
                        "rights_value": "Test Note for Rights",
                    },
                ],
            ),
            (
                TransferStep.OTHER_IDENTIFIERS.value,
                [
                    {
                        "other_identifier_type": "Test Identifier Type",
                        "other_identifier_value": "Test Identifier Value",
                        "other_identifier_note": "Test Identifier Note",
                    },
                ],
            ),
            (
                TransferStep.GROUP_TRANSFER.value,
                {
                    "group_uuid": SubmissionGroup.objects.create(
                        name="Test Group", created_by=self.user
                    ).uuid,
                },
            ),
            (
                TransferStep.UPLOAD_FILES.value,
                {
                    "general_note": "Test General Note",
                },
            )
        ]

        self._test_wizard(self.url, "transfer_form_wizard", data)

    def _get_upload_session_token(self) -> str:
        """Get an upload session token."""
        response = self.client.post(reverse("recordtransfer:create_upload_session"))
        self.assertEqual(201, response.status_code)
        return response.json()["uploadSessionToken"]

    def _upload_test_file(self, session_token: str) -> None:
        """Upload a test file to the server."""
        test_file = SimpleUploadedFile(
            "test_file.txt", b"file_content", content_type="text/plain"
        )
        response = self.client.post(
            reverse("recordtransfer:upload_files", kwargs={"session_token": session_token}),
            {"file": test_file},
        )
        self.assertEqual(200, response.status_code)

    def _test_wizard(self, url: str, name: str, data: list[tuple[str, dict[str, str]]]) -> None:
        """Execute the wizard view installed at the "url", having the given name, with each item
        of data.
        """
        self.assertEqual(200, self.client.get(url).status_code)
        for step, step_data in data:
            post_data = {f"{name}-current_step": step}

            if step == TransferStep.UPLOAD_FILES.value:
                session_token = self._get_upload_session_token()
                post_data[f"{step}-session_token"] = session_token
                self._upload_test_file(session_token)

            if type(step_data) is dict:
                post_data.update(
                    {"{}-{}".format(step, key): value for key, value in step_data.items()}
                )
            elif type(step_data) is list:
                post_data["{}-TOTAL_FORMS".format(step)] = str(len(step_data))
                post_data["{}-INITIAL_FORMS".format(step)] = str(len(step_data))
                for i, item in enumerate(step_data):
                    post_data.update(
                        {"{}-{}-{}".format(step, i, key): value for key, value in item.items()}
                    )

            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(200, response.status_code)
            if "form" in response.context:
                self.assertFalse(response.context["form"].errors)
