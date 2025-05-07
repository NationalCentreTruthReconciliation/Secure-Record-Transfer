import logging
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from caais.models import SourceRole, SourceType, RightsType


class TestHomepage(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def test_index(self):
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
        self.assertContains(response, '<div class="medium-text">Image Files</div>')
        self.assertContains(response, "<li>jpg</li>")
        self.assertContains(response, "<li>png</li>")
        self.assertContains(response, "<li>gif</li>")
        self.assertContains(response, '<div class="medium-text">Document Files</div>')
        self.assertContains(response, "<li>pdf</li>")

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", False)
    def test_accepted_file_types_not_shown(self) -> None:
        """Test that accepted file types are not shown if FILE_UPLOAD_ENABLED is False."""
        response = self.client.get(reverse("recordtransfer:about"))
        self.assertNotContains(response, '<div class="medium-text">Image Files</div>')
        self.assertNotContains(response, '<div class="medium-text">Document Files</div>')

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
        self.assertContains(response, "12 MB")
        self.assertContains(response, "144 MB")
        self.assertContains(response, "100 files")

    @patch("django.conf.settings.FILE_UPLOAD_ENABLED", False)
    def test_file_limits_not_shown(self) -> None:
        """Test that file limits are not shown if FILE_UPLOAD_ENABLED is False."""
        response = self.client.get(reverse("recordtransfer:about"))
        self.assertNotContains(response, "12 MB")
        self.assertNotContains(response, "144 MB")
        self.assertNotContains(response, "100 files")


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
