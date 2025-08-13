import os

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from recordtransfer.models import User

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
class PasswordHistoryAndValidationE2ETest(SeleniumLiveServerTestCase):
    """E2E tests for password change UX: validation, history, and success paths."""

    def setUp(self) -> None:
        """Create a user and log in via the browser session."""
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="InitialPassword123!",
            first_name="Test",
            last_name="User",
            language="en",
        )
        self.login("testuser", "InitialPassword123!")

    def open_profile_and_wait(self) -> None:
        """Navigate to the profile page and wait for password fields to render."""
        profile_url = reverse("recordtransfer:user_profile")
        self.driver.get(f"{self.live_server_url}{profile_url}")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

    def submit_password_change(self, current: str, new: str, confirm: str) -> None:
        """Fill and submit the password change form."""
        self.driver.find_element(By.NAME, "current_password").send_keys(current)
        self.driver.find_element(By.NAME, "new_password").send_keys(new)
        self.driver.find_element(By.NAME, "confirm_new_password").send_keys(confirm)
        save_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_save_button"))
        )
        save_button.click()
