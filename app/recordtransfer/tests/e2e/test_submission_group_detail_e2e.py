import os

from caais.models import Metadata
from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from recordtransfer.models import Submission, SubmissionGroup, User

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
class ChangeSubmissionGroupTest(SeleniumLiveServerTestCase):
    """Test changing the submission group from the profile page."""

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
        self.submission_group = SubmissionGroup.objects.create(
            name="Test Group",
            created_by=self.user,
        )
        self.second_group = SubmissionGroup.objects.create(
            name="Second Group",
            created_by=self.user,
        )
        self.metadata = Metadata.objects.create(accession_title="Test Title")
        self.submission = Submission.objects.create(
            user=self.user,
            metadata=self.metadata,
            part_of_group=self.submission_group,
        )
        self.login("testuser", "testpassword")

    def _click_assign_group_button(self) -> None:
        """Click the assign group button for a submission on the Submission Group Detail page."""
        driver = self.driver
        group_detail_url = reverse(
            "recordtransfer:submission_group_detail", kwargs={"uuid": self.submission_group.uuid}
        )
        driver.get(f"{self.live_server_url}{group_detail_url}")

        # Find the table row containing "Test Title" and click the assign group button
        # First, wait for the table to be present
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))

        # Find all table rows
        table_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

        # Find the row containing "Test Title" and click its assign button
        for row in table_rows:
            submission_title_cell = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)")
            if "Test Title" in submission_title_cell.text:
                assign_button = row.find_element(
                    By.CSS_SELECTOR, "a[id^='assign_submission_group_']"
                )
                assign_button.click()
                break
        else:
            raise AssertionError("Could not find submission with title 'Test Title'")

        # Wait for the modal to appear
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "base_modal")))

        # Wait for the group select dropdown to be present
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "group_select")))

    def test_submission_title_present(self) -> None:
        """Test that the submission title is present in the submission group change modal."""
        driver = self.driver
        self._click_assign_group_button()

        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "assign-group-modal-heading"))
        )

        # Check that the submission title is present in the modal
        modal_title = driver.find_element(By.ID, "assign-group-modal-heading")
        self.assertIn("Test Title", modal_title.text)

    def test_change_submission_group(self) -> None:
        """Test changing the submission group for a submission on the submission group detail
        page.
        """
        driver = self.driver
        self._click_assign_group_button()

        # Wait for the heading and button to be displayed
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "assign-group-modal-heading"))
        )
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "change_group_btn"))
        )

        # Check that modal heading is correct
        modal_heading = driver.find_element(By.ID, "assign-group-modal-heading")
        self.assertIn("Change", modal_heading.text)

        # Check that the change/assign group button contains the correct text
        change_group_button = driver.find_element(By.ID, "change_group_btn")
        self.assertIn("Change", change_group_button.text)

        # Check that the unassign button is present
        unassign_buttons = driver.find_elements(By.ID, "unassign_group_btn")
        self.assertEqual(len(unassign_buttons), 1)

        # Select the group
        group_select = Select(driver.find_element(By.ID, "group_select"))
        group_select.select_by_visible_text("Second Group")

        # Click the change group button
        assign_button = driver.find_element(By.ID, "change_group_btn")
        assign_button.click()

        # Wait for success alert
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "no_groups_msg")))

        # Verify the message text
        no_groups_message = driver.find_element(By.ID, "no_groups_msg")
        self.assertIn("You have not made any submissions in this group", no_groups_message.text)

        # Assert in the database that the submission is assigned to the second group
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.part_of_group, self.second_group)

    def test_change_submission_group_more_than_one_submission_in_current_group(self) -> None:
        """Test changing the submission group when there are multiple submissions in the current
        group.
        """
        driver = self.driver

        # Create another submission in the same group
        Submission.objects.create(
            user=self.user,
            metadata=Metadata.objects.create(accession_title="Second Submission"),
            part_of_group=self.submission_group,
        )

        self._click_assign_group_button()

        # Wait for the heading and button to be displayed
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "assign-group-modal-heading"))
        )
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "change_group_btn"))
        )

        # Select the group
        group_select = Select(driver.find_element(By.ID, "group_select"))
        group_select.select_by_visible_text("Second Group")

        # Click the change group button
        assign_button = driver.find_element(By.ID, "change_group_btn")
        assign_button.click()

        # Wait for success alert
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        # Check that the table updates to show the second submission in the current group
        # Wait for the table to update and check for the second submission
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), "Second Submission")
        )

        # Find all table rows in the tbody
        table_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        self.assertEqual(len(table_rows), 1, "Expected exactly one submission row in the table")

        # Check that the remaining row contains "Second Submission" in the submission title column
        submission_title_cell = table_rows[0].find_element(By.CSS_SELECTOR, "td:nth-child(2)")
        self.assertIn("Second Submission", submission_title_cell.text)

        # Assert in the database that the submission is assigned to the second group
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.part_of_group, self.second_group)

    def test_unassign_submission_group(self) -> None:
        """Test unassigning a submission from its group."""
        # Assign the submission to a group first
        self.submission.part_of_group = self.submission_group
        self.submission.save()

        driver = self.driver
        self._click_assign_group_button()

        # Wait for the heading and button to be displayed
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "assign-group-modal-heading"))
        )
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "unassign_group_btn"))
        )

        # Check that the unassign button is present and click it
        unassign_button = driver.find_element(By.ID, "unassign_group_btn")
        unassign_button.click()

        # Wait for success alert
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )

        # Check that the no groups message is displayed
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "no_groups_msg")))
        no_groups_message = driver.find_element(By.ID, "no_groups_msg")
        self.assertIn("You have not made any submissions in this group", no_groups_message.text)

        # Assert in the database that the submission is no longer assigned to any group
        self.submission.refresh_from_db()
        self.assertIsNone(self.submission.part_of_group)
