from django.test import RequestFactory, TestCase
from django.urls import reverse

from recordtransfer.enums import TransferStep
from recordtransfer.models import User


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
        ]

        self.test_wizard(self.url, "transfer_form_wizard", data)

    def test_wizard(self, url: str, name: str, data: list[tuple[str, dict[str, str]]]) -> None:
        """Using the supplied TestCase, execute the wizard view installed at
        the "url", having the given name, with each item of data.
        """
        self.assertEqual(200, self.client.get(url).status_code)
        for step, step_data in data:
            step_data = {"{}-{}".format(step, key): value for key, value in step_data.items()}
            step_data["{}-current_step".format(name)] = step
            response = self.client.post(url, step_data, follow=True)
            self.assertEqual(200, response.status_code)
            if "form" in response.context:
                self.assertFalse(response.context["form"].errors)
