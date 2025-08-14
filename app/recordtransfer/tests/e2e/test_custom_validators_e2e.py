import os
from unittest.mock import MagicMock, patch

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
class CustomValidatorsE2ETest(SeleniumLiveServerTestCase):
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

    @patch("recordtransfer.views.profile.send_user_account_updated")
    def test_successful_password_change_shows_success(self, email_mock: MagicMock) -> None:
        """Shows a success alert when changing password with valid inputs."""
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="SecondPassword456!",
            confirm="SecondPassword456!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

    def test_same_as_current_password_shows_field_error(self) -> None:
        """Displays field error when new password equals current password."""
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="InitialPassword123!",
            confirm="InitialPassword123!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your new password cannot be the same as your current password." in page_text

    def test_too_short_password_shows_error(self) -> None:
        """Displays validation error for too short password."""
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="Short1!",
            confirm="Short1!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "This password is too short" in page_text

    def test_too_long_password_shows_error(self) -> None:
        """Displays validation error for too long password."""
        self.open_profile_and_wait()
        long_pwd = "A" * 31 + "1!a"
        self.submit_password_change(
            current="InitialPassword123!",
            new=long_pwd,
            confirm=long_pwd,
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "This password is too long" in page_text

    def test_missing_character_categories_shows_error(self) -> None:
        """Displays validation error when required character categories are missing."""
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="Onlylettersandnumbers",
            confirm="Onlylettersandnumbers",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your password must contain at least" in page_text

        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="onlylettersandspecialchars!",
            confirm="onlylettersandspecialchars!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your password must contain at least" in page_text

        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="ONLYUPPERLETTERSANDNUMBERS",
            confirm="ONLYUPPERLETTERSANDNUMBERS",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your password must contain at least" in page_text

    @patch("recordtransfer.views.profile.send_user_account_updated")
    def test_reuse_previous_passwords_shows_error(self, email_mock: MagicMock) -> None:
        """Displays validation error when attempting to reuse a previous password."""
        self.open_profile_and_wait()
        # Build history with multiple changes
        sequence = [
            ("InitialPassword123!", "SecondPassword456!"),
            ("SecondPassword456!", "ThirdPassword789!"),
            ("ThirdPassword789!", "FourthPasswordABC!"),
            ("FourthPasswordABC!", "FifthPasswordDEF!"),
            ("FifthPasswordDEF!", "SixthPasswordXYZ!"),
        ]
        for current, new in sequence:
            self.submit_password_change(current=current, new=new, confirm=new)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
            # return to ensure form ready for next iteration
            self.open_profile_and_wait()

        # Try to reuse an older password (e.g., SecondPassword456!)
        self.submit_password_change(
            current="SixthPasswordXYZ!",
            new="SecondPassword456!",
            confirm="SecondPassword456!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "You cannot reuse your previous 5 passwords." in page_text

    def test_password_contains_username_shows_error(self) -> None:
        """Displays error when password contains the user's exact username."""
        self.user.username = "ExactUserName"
        self.user.save()
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="ExactUserName-Strong1!",
            confirm="ExactUserName-Strong1!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your password cannot contain your first name, last name, or username." in page_text

    def test_password_contains_first_name_shows_error(self) -> None:
        """Displays error when password contains the user's exact first name."""
        self.user.first_name = "Firstname"
        self.user.save()
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="Firstname-Strong1!",
            confirm="Firstname-Strong1!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your password cannot contain your first name, last name, or username." in page_text

    def test_password_contains_last_name_shows_error(self) -> None:
        """Displays error when password contains the user's exact last name."""
        self.user.last_name = "Lastname"
        self.user.save()
        self.open_profile_and_wait()
        self.submit_password_change(
            current="InitialPassword123!",
            new="Lastname-Strong1!",
            confirm="Lastname-Strong1!",
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        page_text = self.driver.page_source
        assert "Your password cannot contain your first name, last name, or username." in page_text
