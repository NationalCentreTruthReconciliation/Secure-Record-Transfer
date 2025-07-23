import logging
from unittest.mock import patch

from caais.models import RightsType, SourceRole, SourceType
from django.test import TestCase
from django.urls import reverse


class TestHomepage(TestCase):
    """Test homepage contents."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def test_index(self) -> None:
        """Test that the index page loads successfully."""
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NCTR Record Transfer")


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Image": ["jpg", "png", "gif"], "Document": ["pdf"]},
)
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE_MB", 12)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE_MB", 144)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_COUNT", 100)
class TestAboutPage(TestCase):
    """Test about page contents."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create sample objects to be rendered on about page."""
        super().setUpClass()

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", True)
    def test_accepted_file_types_shown(self) -> None:
        """Test that accepted file types are shown when FILE_UPLOAD_ENABLED is True."""
        response = self.client.get(reverse("recordtransfer:about"))
        self.assertIn("ACCEPTED_FILE_FORMATS", response.context)
        self.assertContains(response, "Image Files")
        print(response.content.decode())
        self.assertContains(response, "jpg")
        self.assertContains(response, "png")
        self.assertContains(response, "gif")
        self.assertContains(response, "Document Files")
        self.assertContains(response, "pdf")

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", False)
    def test_accepted_file_types_not_shown(self) -> None:
        """Test that accepted file types are not shown if FILE_UPLOAD_ENABLED is False."""
        response = self.client.get(reverse("recordtransfer:about"))
        self.assertNotContains(response, "Image Files")
        self.assertNotContains(response, "Document Files")

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", True)
    def test_file_limits_shown(self) -> None:
        """Test that file limits are shown when FILE_UPLOAD_ENABLED is True."""
        response = self.client.get(reverse("recordtransfer:about"))
        self.assertIn("MAX_SINGLE_UPLOAD_SIZE_MB", response.context)
        self.assertIn("MAX_TOTAL_UPLOAD_SIZE_MB", response.context)
        self.assertIn("MAX_TOTAL_UPLOAD_COUNT", response.context)
        self.assertEqual(response.context["MAX_SINGLE_UPLOAD_SIZE_MB"], 12)
        self.assertEqual(response.context["MAX_TOTAL_UPLOAD_SIZE_MB"], 144)
        self.assertEqual(response.context["MAX_TOTAL_UPLOAD_COUNT"], 100)
        self.assertContains(response, "maximum of 100 files")
        self.assertContains(response, "144 MB of files")
        self.assertContains(response, "12 MB")

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", False)
    def test_file_limits_not_shown(self) -> None:
        """Test that file limits are not shown if FILE_UPLOAD_ENABLED is False."""
        response = self.client.get(reverse("recordtransfer:about"))
        self.assertNotContains(response, "maximum of 100 files")
        self.assertNotContains(response, "144 MB of files")
        self.assertNotContains(response, "12 MB")


class TestHelpPage(TestCase):
    """Test help page contents."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create sample objects to be rendered on about page."""
        super().setUpClass()
        cls.sample_stype, _ = SourceType.objects.get_or_create(
            name="Sample Source Type", description="Description for sample source type."
        )
        cls.sample_srole, _ = SourceRole.objects.get_or_create(
            name="Sample Source Role", description="Description for sample source role."
        )
        cls.sample_rtype, _ = RightsType.objects.get_or_create(
            name="Sample Rights Type", description="Description for sample rights type."
        )

    def test_source_types_in_context(self) -> None:
        """Test that source types are passed to the template context."""
        response = self.client.get(reverse("recordtransfer:help"))
        self.assertIn("source_roles", response.context)
        self.assertIn(self.sample_stype, response.context["source_types"])
        self.assertContains(response, "Description for sample source type.")

    def test_source_roles_in_context(self) -> None:
        """Test that source roles are passed to the template context."""
        response = self.client.get(reverse("recordtransfer:help"))
        self.assertIn("source_roles", response.context)
        self.assertIn(self.sample_srole, response.context["source_roles"])
        self.assertContains(response, "Description for sample source role.")

    def test_rights_type_in_context(self) -> None:
        """Test that rights types are passed to the template context."""
        response = self.client.get(reverse("recordtransfer:help"))
        self.assertIn("rights_types", response.context)
        self.assertIn(self.sample_rtype, response.context["rights_types"])
        self.assertContains(response, "Description for sample rights type.")
