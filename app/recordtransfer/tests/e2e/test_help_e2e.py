import os

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from recordtransfer.tests.e2e.selenium_setup import SeleniumLiveServerTestCase


@tag("e2e")
@override_settings(
    WEBPACK_LOADER={
        "DEFAULT": {
            "STATS_FILE": os.path.join(
                os.path.dirname(settings.APPLICATION_BASE_DIR), "dist", "webpack-stats.json"
            ),
        },
    }
)
class HelpPageTest(SeleniumLiveServerTestCase):
    """End-to-end tests for the Help page."""

    def test_help_page_loads(self) -> None:
        """Test that the Help page loads and displays correct heading."""
        driver = self.driver
        help_url = reverse("recordtransfer:help")
        driver.get(f"{self.live_server_url}{help_url}")

        # Check the page heading (it's a div, not h1)
        page_heading = driver.find_element(By.ID, "help-page-heading")
        self.assertIn("Help", page_heading.text)

    def test_help_page_structure(self) -> None:
        """Test that the Help page contains all required sections."""
        driver = self.driver
        help_url = reverse("recordtransfer:help")
        driver.get(f"{self.live_server_url}{help_url}")

        # Check for the three main help cards
        help_sections = ["source-types", "source-roles", "rights-types"]

        for section_id in help_sections:
            section = driver.find_element(By.ID, section_id)
            self.assertTrue(section.is_displayed(), f"Section {section_id} should be visible")

    def test_navigation_to_help_page(self) -> None:
        """Test navigating to the Help page from the homepage."""
        driver = self.driver
        # Start at homepage
        driver.get(f"{self.live_server_url}/")

        # Find and click the Help link in the navigation

        help_link = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "nav-help")))
        help_link.click()

        # Verify we're on the Help page
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "help-page-heading"))
        )
        self.assertIn("help", driver.current_url)
