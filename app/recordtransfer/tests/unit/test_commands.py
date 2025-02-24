from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import TestCase


class TestSetDomain(TestCase):
    """Test setting the domain and display name with the set_domain command."""

    def setUp(self) -> None:
        """Set up test environment with initial site state."""
        self.original_name = "My Site"
        self.original_domain = "my.example.com"
        self.site = Site.objects.get_current()
        self.site.name = self.original_name
        self.site.domain = self.original_domain
        self.site.save()

    def tearDown(self) -> None:
        """Reset site to original state after each test."""
        self.site.domain = self.original_domain
        self.site.name = self.original_name
        self.site.save()

    def test_set_domain_command(self) -> None:
        """Test that the command updates the site domain."""
        call_command("set_domain", "test.example.com")
        updated_site = Site.objects.get_current()
        self.assertEqual(updated_site.domain, "test.example.com")
        self.assertEqual(updated_site.name, self.original_name)

    def test_set_domain_with_name(self) -> None:
        """Test that the command updates both domain and name."""
        call_command("set_domain", "www.example.com", display_name="Test Site")
        updated_site = Site.objects.get_current()
        self.assertEqual(updated_site.domain, "www.example.com")
        self.assertEqual(updated_site.name, "Test Site")

    def test_set_name_with_same_domain(self) -> None:
        """Test that the command updates both domain and name."""
        call_command("set_domain", self.original_domain, display_name="Changed Site Name")
        updated_site = Site.objects.get_current()
        self.assertEqual(updated_site.domain, self.original_domain)
        self.assertEqual(updated_site.name, "Changed Site Name")

    def test_set_domain_with_spaces_in_name(self) -> None:
        """Test that the command returns early before setting an invalid name with whitespace."""
        call_command("set_domain", "mysite ca")
        updated_site = Site.objects.get_current()
        self.assertEqual(updated_site.domain, self.original_domain)
        self.assertEqual(updated_site.name, self.original_name)

    def test_set_domain_starts_with_https(self) -> None:
        """Test that the command returns early before setting a domain starting with https://."""
        invalid = ("http://domain.ca", "https://domain.ca")

        for value in invalid:
            with self.subTest(value):
                call_command("set_domain", value)
                updated_site = Site.objects.get_current()
                self.assertEqual(updated_site.domain, self.original_domain)
                self.assertEqual(updated_site.name, self.original_name)
