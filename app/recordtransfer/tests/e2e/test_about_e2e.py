import os

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .selenium_setup import SeleniumLiveServerTestCase


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
class AboutPageE2ETests(SeleniumLiveServerTestCase):
    """End-to-end tests for the About page."""

    def test_about_page_loads(self) -> None:
        """Test that the About page loads and displays correct heading."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Check the page heading (it's a div, not h1)
        page_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "about-page-heading"))
        )
        self.assertIn("About", page_heading.text)
