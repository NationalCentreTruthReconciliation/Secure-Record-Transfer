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

        page_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "about-page-heading"))
        )
        self.assertIn("About", page_heading.text)

    def test_a(self) -> None:
        """Test navigation from home page to About page without login."""
        driver = self.driver
        home_url = reverse("recordtransfer:index")
        driver.get(f"{self.live_server_url}{home_url}")

        about_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "nav-about"))
        )
        about_link.click()

        page_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "about-page-heading"))
        )
        self.assertIn("About", page_heading.text)

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        MAX_TOTAL_UPLOAD_COUNT=100,
        MAX_TOTAL_UPLOAD_SIZE_MB=144,
        MAX_SINGLE_UPLOAD_SIZE_MB=12,
    )
    def test_file_upload_info_shown_when_enabled(self) -> None:
        """Test that file upload info is displayed when uploads are enabled."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Check that file size limitations are displayed
        max_size_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Maximum Submission Size')]")
            )
        )
        self.assertIsNotNone(max_size_heading)

        # Check specific values
        page_content = driver.page_source
        self.assertIn("maximum of 100 files", page_content)
        self.assertIn("144 MB of files", page_content)
        self.assertIn("12 MB", page_content)

    @override_settings(FILE_UPLOAD_ENABLED=False)
    def test_file_upload_info_hidden_when_disabled(self) -> None:
        """Test that file upload info is not displayed when uploads are disabled."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Wait for page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card-body p"))
        )

        # Check that file size limitations are NOT displayed
        page_content = driver.page_source
        self.assertNotIn("Maximum Submission Size", page_content)

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        ACCEPTED_FILE_FORMATS={"Image": ["jpg", "png", "gif"], "Document": ["pdf"]},
    )
    def test_accepted_file_types_displayed(self) -> None:
        """Test that accepted file types are correctly displayed."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Check for file type categories
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Accepted File Types')]")
            )
        )

        # Check that specific file types are listed
        page_content = driver.page_source
        self.assertIn("Image Files", page_content)
        self.assertIn("jpg", page_content)
        self.assertIn("png", page_content)
        self.assertIn("gif", page_content)
        self.assertIn("Document Files", page_content)
        self.assertIn("pdf", page_content)

    def test_page_responsiveness(self) -> None:
        """Test that the About page is responsive at different viewport sizes."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")

        # Test desktop size
        driver.set_window_size(1200, 800)
        driver.get(f"{self.live_server_url}{about_url}")
        desktop_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        self.assertTrue(desktop_element.is_displayed())

        # Test tablet size
        driver.set_window_size(768, 1024)
        driver.get(f"{self.live_server_url}{about_url}")
        tablet_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        self.assertTrue(tablet_element.is_displayed())

        # Test mobile size
        driver.set_window_size(375, 667)
        driver.get(f"{self.live_server_url}{about_url}")
        mobile_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        self.assertTrue(mobile_element.is_displayed())
