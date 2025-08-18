import os
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from recordtransfer.models import User
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
@patch("recordtransfer.emails.send_user_account_updated.delay")
class ChangePasswordTest(SeleniumLiveServerTestCase):
    """End-to-end tests for the Change Password page."""

    def setUp(self) -> None:
        """Set up test data and log in the test user."""
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Securepassword123",
            first_name="Test",
            last_name="User",
            language="en",
        )
        self.login("testuser", "Securepassword123")

        change_password_url = reverse("password_change")
        self.driver.get(f"{self.live_server_url}{change_password_url}")

        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_old_password"))
        )

    def test_change_password_valid(self, mock_send_email: MagicMock) -> None:
        """Test changing the password with valid data."""
        new_password = "NewSecurepassword123"
        self.driver.find_element(By.ID, "id_old_password").send_keys("Securepassword123")
        self.driver.find_element(By.ID, "id_new_password1").send_keys(new_password)
        self.driver.find_element(By.ID, "id_new_password2").send_keys(new_password)
        self.driver.find_element(By.ID, "id_change_password_button").click()

        # Wait to redirect to password change done page
        WebDriverWait(self.driver, 10).until(EC.url_contains(reverse("password_change_done")))

        # Verify the email function was called
        mock_send_email.assert_called_once()

        # Verify the password has been changed by logging out and back in
        logout_button = self.driver.find_element(By.ID, "logout-btn")
        self.driver.execute_script("arguments[0].click();", logout_button)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "nav-login")))
        self.login("testuser", new_password)

    def test_wrong_old_password(self, mock_send_email: MagicMock) -> None:
        """Test changing the password with an incorrect old password."""
        self.driver.find_element(By.ID, "id_old_password").send_keys("WrongOldPassword")
        self.driver.find_element(By.ID, "id_new_password1").send_keys("NewSecurepassword123")
        self.driver.find_element(By.ID, "id_new_password2").send_keys("NewSecurepassword123")
        self.driver.find_element(By.ID, "id_change_password_button").click()

        # Check for error message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-error"))
        )
