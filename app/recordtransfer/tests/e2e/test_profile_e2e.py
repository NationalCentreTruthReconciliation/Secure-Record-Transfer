import os
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from recordtransfer.models import InProgressSubmission, Metadata, Submission, SubmissionGroup, User

from .selenium_setup import SeleniumLiveServerTestCase


@tag("e2e")
@override_settings(
    WEBPACK_LOADER={
        "DEFAULT": {
            # TODO: This is not working yet!
            "STATS_FILE": "dist/webpack-stats.json",
        },
    }
)
class ProfilePasswordResetTest(SeleniumLiveServerTestCase):
    def setUp(self) -> None:
        """Set up test data and log in the test user."""
        super().setUp()
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

        self.submission_group = SubmissionGroup.objects.create(
            name="Test Group",
            created_by=self.user,
        )
        self.login("testuser", "testpassword")

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

    def create_in_progress_submission(self) -> InProgressSubmission:
        """Create an in-progress submission for the current user and return it.
        Moved to second page as it needed to have click on the "Save for later" button.
        """
        driver = self.driver
        # Go to the new submission page
        new_submission_url = reverse("recordtransfer:submit")
        driver.get(f"{self.live_server_url}{new_submission_url}")

        # Fill the first page (accept legal)
        checkbox = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.NAME, "acceptlegal-agreement_accepted"))
        )
        checkbox.click()

        # Click "Next" to go to the next page
        next_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "form-next-button"))
        )
        next_btn.click()

        # Click "Save for later"
        save_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "form-save-button"))
        )
        save_btn.click()

        # Wait for success alert
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        # Now fetch the submission from the DB
        submission = InProgressSubmission.objects.filter(user=self.user).order_by("-pk").first()
        assert submission is not None
        return submission

    def move_to_submission_groups(self) -> None:
        """Help method to move to an in-progress submission."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        # Find the label for the in-progress tab by 'for' attribute or by containing the input
        submission_group_label = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//label[input[@id='id_submission_group_tab']]"))
        )
        submission_group_label.click()

    @patch("recordtransfer.views.profile.send_user_account_updated")
    def test_reset_password_from_profile(self, email_mock: MagicMock) -> None:
        """Test resetting the password from the profile page."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        save_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_save_button"))
        )
        save_button.click()

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        from django.contrib.auth import get_user_model

        user = get_user_model().objects.get(username="testuser")
        self.assertTrue(user.check_password("newsecurepassword"))

    def test_profile_password_change_wrong_current_password(self) -> None:
        """Test error when the current password is wrong."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

        driver.find_element(By.NAME, "current_password").send_keys("wrongpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")
        save_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_save_button"))
        )
        save_button.click()

        error_present = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        alert_present = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-error"))
        )
        self.assertTrue(error_present and alert_present)

    def test_profile_password_change_mismatched_new_passwords(self) -> None:
        """Test error when new passwords do not match."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("differentpassword")
        save_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_save_button"))
        )
        save_button.click()

        error_present = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        alert_present = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-error"))
        )
        self.assertTrue(error_present and alert_present)

    def test_submission_view_from_profile(self) -> None:
        """Test that the submission view can be accessed from the profile page."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        submission_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "view_submission_report_1"))
        )
        original_window = driver.current_window_handle

        submission_link.click()

        # Get all window handles
        all_windows = driver.window_handles

        new_window = next(window for window in all_windows if window != original_window)
        driver.switch_to.window(new_window)

        # Increase timeout and add more specific waiting
        submission_report_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[starts-with(text(), 'Submission Report for')]")
            )
        )

        self.assertIsNotNone(submission_report_heading)

    def test_download_submission_CSV_for_profile(self) -> None:
        """Test downloading the submission report from the profile page."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        # Find the download button and check its href
        download_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "id_download_csv_1"))
        )
        download_url = download_button.get_attribute("href")

        # Build the expected URL using Django's reverse and the submission's UUID
        expected_url = f"{self.live_server_url}{reverse('recordtransfer:submission_csv', kwargs={'uuid': str(self.submission.uuid)})}"
        self.assertEqual(download_url, expected_url)

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
        expected_url = f"{self.live_server_url}{reverse('recordtransfer:submit')}"

        self.assertEqual(current_url, expected_url)

    def test_edit_profile_settings(self) -> None:
        """Test editing profile settings from the profile page."""
        driver = self.driver
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        # First two fields: should be editable
        first_name_input = driver.find_element(By.ID, "id_first_name")
        last_name_input = driver.find_element(By.ID, "id_last_name")
        # Last two fields: should NOT be editable/clickable
        email_input = driver.find_element(By.ID, "id_email")
        username_input = driver.find_element(By.ID, "id_username")
        notifications_checkbox = driver.find_element(By.ID, "id_gets_notification_emails")

        # Check first two are enabled and editable
        self.assertTrue(first_name_input.is_enabled())
        self.assertTrue(last_name_input.is_enabled())
        first_name_input.clear()
        last_name_input.clear()
        first_name_input.send_keys("EditedFirst")
        last_name_input.send_keys("EditedLast")
        initial_state = notifications_checkbox.is_selected()

        # Toggle the checkbox
        notifications_checkbox.click()

        # Check last two are disabled (not editable/clickable)
        self.assertFalse(email_input.is_enabled())
        self.assertFalse(username_input.is_enabled())

        # Click save
        save_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_save_button"))
        )
        save_button.click()

        # Wait for success alert
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        # Check if the changes persisted
        first_name_input = driver.find_element(By.ID, "id_first_name")
        last_name_input = driver.find_element(By.ID, "id_last_name")
        self.assertEqual(first_name_input.get_attribute("value"), "EditedFirst")
        self.assertEqual(last_name_input.get_attribute("value"), "EditedLast")

        notifications_checkbox = driver.find_element(By.ID, "id_gets_notification_emails")
        self.assertNotEqual(notifications_checkbox.is_selected(), initial_state)

    def test_resume_in_progress_submission(self) -> None:
        """Test resuming an in-progress submission from the profile page."""
        driver = self.driver
        self.in_progress_submission = self.create_in_progress_submission()
        self.move_to_in_progress_submission()

        # Wait for the resume button to be present
        resume_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "resume_in_progress_1"))
        )

        resume_button.click()

        # Assert that you are now on the resume page (adjust as needed)
        WebDriverWait(driver, 5).until(EC.url_contains("resume"))
        expected_query = f"resume={self.in_progress_submission.uuid}"
        parsed_url = urlparse(driver.current_url)

        self.assertEqual(reverse("recordtransfer:submit"), parsed_url.path)
        self.assertIn(expected_query, parsed_url.query)

    def test_resume_does_not_duplicate_in_progress(self) -> None:
        """Test that resuming an in-progress submission does not create a duplicate."""
        driver = self.driver
        self.create_in_progress_submission()
        self.move_to_in_progress_submission()

        resume_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "resume_in_progress_1"))
        )

        resume_button.click()

        # Now click the "Save for later" button
        save_for_later = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "form-save-button"))
        )
        save_for_later.click()

        # # Assert only one InProgressSubmission exists for this user
        in_progress_count = InProgressSubmission.objects.filter(user=self.user).count()
        self.assertEqual(in_progress_count, 1)

    def test_delete_in_progress_submission(self) -> None:
        """Test deleting an in-progress submission from the profile page."""
        driver = self.driver
        self.in_progress_submission = self.create_in_progress_submission()
        self.move_to_in_progress_submission()
        # Click the delete button in that row (adjust class or selector if needed)
        delete_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "delete_in_progress_1"))
        )
        delete_button.click()

        # Wait for the "Yes" button to be clickable and click it
        confirm_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "confirm_delete_ip_btn"))
        )
        confirm_button.click()

        # Wait for the row to be removed or for a "no submissions" message
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "empty_in_progress_submission"))
        )

        # Assert in the database that the in-progress submission is deleted
        exists = InProgressSubmission.objects.filter(pk=self.in_progress_submission.pk).exists()
        self.assertFalse(exists)

    def test_new_submission_group(self) -> None:
        """Test creating a new submission group from the profile page."""
        driver = self.driver
        self.move_to_submission_groups()

        # Click the new submission group button
        new_group_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_new_submission_group_button"))
        )
        new_group_button.click()

        # Wait for the modal to appear and fill in the form
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-box"))
        )
        group_name_input = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_submission_group_name"))
        )
        group_name_input.send_keys("Test Submission Group")
        # Submit the form
        submit_button = driver.find_element(By.ID, "id_create_group_button")
        submit_button.click()

        # Check if the group was created successfully
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        # Assert in the database that the group exists
        exists = SubmissionGroup.objects.filter(name="Test Submission Group").exists()
        self.assertTrue(exists)

    def test_view_submission_group(self) -> None:
        """Test viewing a submission group from the profile page."""
        driver = self.driver
        self.move_to_submission_groups()

        # Click the link to view the submission group
        group_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "view_submission_group_1"))
        )

        group_link.click()

        # Wait for the URL to update and check it contains 'submission-group'
        WebDriverWait(driver, 5).until(lambda d: "submission-group" in d.current_url)

        # Assert that the current URL is the expected one
        exoected_url = f"{self.live_server_url}{reverse('recordtransfer:submission_group_detail', kwargs={'uuid': str(self.submission_group.uuid)})}"
        self.assertEqual(driver.current_url, exoected_url)

    def test_delete_submission_group(self) -> None:
        """Test deleting a submission group from the profile page."""
        driver = self.driver
        self.move_to_submission_groups()

        # Click the delete button in that row (adjust class or selector if needed)
        delete_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "delete_submission_group_1"))
        )
        delete_button.click()

        confirm_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "confirm_delete_submission_group_btn"))
        )
        confirm_button.click()

        # Wait for the row to be removed or for a "no submissions" message
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        # Assert in the database that the submission group is deleted
        exists = SubmissionGroup.objects.filter(pk=self.submission_group.pk).exists()
        self.assertFalse(exists)

    def test_duplicate_submission_group_name_not_allowed(self) -> None:
        """Test that creating a submission group with a duplicate name is not allowed."""
        driver = self.driver
        self.move_to_submission_groups()

        # Try to create a duplicate group with the same name as in setUp
        new_group_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_new_submission_group_button"))
        )
        new_group_button.click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-box"))
        )
        group_name_input = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_submission_group_name"))
        )
        group_name_input.clear()
        group_name_input.send_keys("Test Group")
        submit_button = driver.find_element(By.ID, "id_create_group_button")
        submit_button.click()

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-box"))
        )

        # Assert an error message is shown
        error_present = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "text-error"))
        )
        self.assertIsNotNone(error_present)
