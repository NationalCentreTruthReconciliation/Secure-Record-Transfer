from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from unittest.mock import patch, MagicMock

from recordtransfer.models import (
    User,
    Submission,
    Metadata,
    InProgressSubmission,
)


@tag("e2e")
class ProfilePasswordResetTest(StaticLiveServerTestCase):
    def setUp(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-autofill")
        chrome_options.add_argument("--disable-save-password-bubble")
        if settings.SELENIUM_TESTS_HEADLESS_MODE:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--guest")
        prefs = {"autofill.profile_enabled": False}
        chrome_options.add_experimental_option("prefs", prefs)

        # Set up the web driver (e.g., Chrome)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )
        self.metadata = Metadata.objects.create()

        self.submission = Submission.objects.create(
            user=self.user,
            metadata=self.metadata,
        )
        # Create the InProgressSubmission
        self.in_progress_submission = InProgressSubmission.objects.create(
            user=self.user,
        )
        self.login()

    def tearDown(self) -> None:
        """Tear down the test case by quitting the web driver."""
        self.driver.quit()

    def login(self) -> None:
        """Log in the test user."""
        driver = self.driver
        login_url = reverse("login")
        driver.get(f"{self.live_server_url}{login_url}")

        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys("testuser")
        password_input.send_keys("testpassword")
        password_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "logout-btn")))

    @patch("recordtransfer.views.profile.send_user_account_updated")
    def test_reset_password_from_profile(self, email_mock: MagicMock) -> None:
        """Test resetting the password from the profile page."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        save_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "id_save_button"))
        )
        save_button.click()

        try:
            success_alert = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
            print("Success alert found: ", success_alert.text)

        except Exception as e:
            print("Failed to find success alert.")
            print(driver.page_source)
            self.fail(f"Success alert not found: {e}")

    def test_submission_view_from_profile(self) -> None:
        """Test that the submission view can be accessed from the profile page."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        submission_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "link-info"))
        )
        original_window = driver.current_window_handle

        submission_link.click()

        # Get all window handles
        all_windows = driver.window_handles

        new_window = next(window for window in all_windows if window != original_window)
        driver.switch_to.window(new_window)

        try:
            # Increase timeout and add more specific waiting
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[starts-with(text(), 'Submission Report for')]")
                )
            )
        except Exception as e:
            print(f"FAILED to find main-title: {e}")
            self.fail("Could not find main-title element")

    def test_new_submission_button_from_profile(self) -> None:
        """Test that the new submission button from the profile page works correctly."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        # Wait for and click the new submission button
        new_submission_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_new_submission_button"))
        )
        new_submission_button.click()

        current_url = driver.current_url

        # Check if URL contains 'submission'
        self.assertIn(
            "submission",
            current_url.lower(),
        )

    def move_to_in_progress_submission(self) -> None:
        """Help method to move to an in-progress submission."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        # Find the label for the in-progress tab by 'for' attribute or by containing the input
        in_progress_label = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//label[input[@id='id_in_progress_tab']]"))
        )
        in_progress_label.click()

    def test_resume_in_progress_submission(self) -> None:
        """Test resuming an in-progress submission from the profile page."""
        driver = self.driver
        self.move_to_in_progress_submission()
        resume_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "resume-in-progress"))
        )

        resume_button.click()

        # Assert that you are now on the resume page (adjust as needed)
        WebDriverWait(driver, 10).until(EC.url_contains("resume"))
        self.assertIn("resume", driver.current_url)

    def test_delete_in_progress_submission(self) -> None:
        """Test deleting an in-progress submission from the profile page."""
        driver = self.driver
        self.move_to_in_progress_submission()

        # Click the delete button in that row (adjust class or selector if needed)
        delete_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "delete-in-progress"))
        )
        delete_button.click()

        # If a confirmation dialog appears, accept it
        try:
            # Wait for the "Yes" button to be clickable and click it
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "confirm_delete_ip_btn"))
            )
            confirm_button.click()
        except Exception:
            print("No alert appeared, proceeding without confirmation.")
            pass  # No alert appeared

        # Wait for the row to be removed or for a "no submissions" message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "empty_in_progress_submission"))
        )
