import os
from unittest.mock import patch

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from recordtransfer.models import User


class TransferFormWizardTest(LiveServerTestCase):
    """End-to-end tests for the transfer form wizard."""

    def setUp(self) -> None:
        """Set up the web driver and create a test user."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-autofill")
        chrome_options.add_argument("--disable-save-password-bubble")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        prefs = {"autofill.profile_enabled": False}
        chrome_options.add_experimental_option("prefs", prefs)

        # Set up the web driver (e.g., Chrome)
        self.driver = webdriver.Chrome(options=chrome_options)

        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def tearDown(self) -> None:
        """Close the web driver."""
        self.driver.quit()

    def login(self) -> None:
        """Log in the test user."""
        driver = self.driver

        # Open the login page
        driver.get(f"{self.live_server_url}/accounts/login/")

        # Log in
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys("testuser")
        password_input.send_keys("testpassword")
        password_input.send_keys(Keys.RETURN)

        # Wait for the login to complete and redirect to the home page
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "logout-btn")))

    def go_next_step(self) -> None:
        driver = self.driver
        driver.find_element(By.ID, "form-next-button").click()

    def go_previous_step(self) -> None:
        driver = self.driver
        driver.find_element(By.ID, "form-previous-button").click()

    def complete_legal_agreement_step(self) -> None:
        driver = self.driver

        # Complete the Legal Agreement step
        accept_agreement_checkbox = driver.find_element(By.NAME, "acceptlegal-agreement_accepted")
        accept_agreement_checkbox.click()
        driver.find_element(By.ID, "form-next-button").click()

    def complete_contact_information_step(self, required_only: bool = False) -> None:
        driver = self.driver

        # Complete the Contact Information step
        contact_name_input = driver.find_element(By.NAME, "contactinfo-contact_name")
        phone_number_input = driver.find_element(By.NAME, "contactinfo-phone_number")
        email_input = driver.find_element(By.NAME, "contactinfo-email")
        address_line_1_input = driver.find_element(By.NAME, "contactinfo-address_line_1")
        city_input = driver.find_element(By.NAME, "contactinfo-city")
        province_or_state_input = driver.find_element(By.NAME, "contactinfo-province_or_state")
        postal_or_zip_code_input = driver.find_element(By.NAME, "contactinfo-postal_or_zip_code")
        country_input = driver.find_element(By.NAME, "contactinfo-country")

        contact_name_input.send_keys("John Doe")
        phone_number_input.send_keys("+1 (999) 999-9999")
        email_input.send_keys("john.doe@example.com")
        address_line_1_input.send_keys("123 Main St")
        city_input.send_keys("Winnipeg")
        province_or_state_input.send_keys("MB")
        postal_or_zip_code_input.send_keys("R3C 1A5")
        country_input.send_keys("CA")

        if not required_only:
            job_title_input = driver.find_element(By.NAME, "contactinfo-job_title")
            organization_input = driver.find_element(By.NAME, "contactinfo-organization")

            job_title_input.send_keys("Archivist")
            organization_input.send_keys("Test Organization")

        self.go_next_step()

    def complete_source_information_step(self, required_only: bool = False) -> None:
        driver = self.driver

        # Complete the Source Information step
        enter_manual_source_info_radio_0 = driver.find_element(
            By.NAME, "sourceinfo-enter_manual_source_info"
        )
        # Click yes
        enter_manual_source_info_radio_0.click()

        source_name_input = driver.find_element(By.NAME, "sourceinfo-source_name")
        source_type_select = Select(driver.find_element(By.NAME, "sourceinfo-source_type"))
        source_role_select = Select(driver.find_element(By.NAME, "sourceinfo-source_role"))

        source_name_input.send_keys("Test Source Name")
        source_type_select.select_by_value("2")  # Select "Individual"
        source_role_select.select_by_value("2")  # Select "Donor"

        if not required_only:
            source_note_input = driver.find_element(By.NAME, "sourceinfo-source_note")
            preliminary_custodial_history = driver.find_element(
                By.NAME, "sourceinfo-preliminary_custodial_history"
            )

            source_note_input.send_keys("Test Source Note")
            preliminary_custodial_history.send_keys("Test Custodial History")

        self.go_next_step()

    def complete_record_description_step(self, required_only: bool = False) -> None:
        accession_title_input = self.driver.find_element(
            By.NAME, "recorddescription-accession_title"
        )
        start_date_input = self.driver.find_element(
            By.NAME, "recorddescription-start_date_of_material"
        )
        end_date_input = self.driver.find_element(
            By.NAME, "recorddescription-end_date_of_material"
        )
        language_input = self.driver.find_element(
            By.NAME, "recorddescription-language_of_material"
        )
        description_of_contents_input = self.driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        accession_title_input.send_keys("Test Accession Title")
        start_date_input.send_keys("2021-01-01")
        end_date_input.send_keys("2021-12-31")
        language_input.send_keys("English")
        description_of_contents_input.send_keys("Test Description")

        if not required_only:
            condition_input = self.driver.find_element(
                By.NAME, "recorddescription-condition_assessment"
            )

            condition_input.send_keys("Test Condition")

        self.go_next_step()

    def complete_record_rights_step(self, required_only: bool = False) -> None:
        driver = self.driver

        # Complete the Record Rights step
        rights_type_select = Select(driver.find_element(By.NAME, "rights-0-rights_type"))
        rights_value_textarea = driver.find_element(By.NAME, "rights-0-rights_value")

        rights_type_select.select_by_value("7")  # Select "Copyright"
        if not required_only:
            rights_value_textarea.send_keys("Copyright until 2050, applies to all files")

        self.go_next_step()

    def complete_other_identifiers_step(self, required_only: bool = False) -> None:
        if required_only:
            self.go_next_step()
            return

        driver = self.driver

        # Complete the Other Identifiers step
        identifier_type_input = driver.find_element(
            By.NAME, "otheridentifiers-0-other_identifier_type"
        )
        identifier_value_input = driver.find_element(
            By.NAME, "otheridentifiers-0-other_identifier_value"
        )

        identifier_type_input.send_keys("Receipt number")
        identifier_value_input.send_keys("123456")

        identifier_note_input = driver.find_element(
            By.NAME, "otheridentifiers-0-other_identifier_note"
        )
        identifier_note_input.send_keys("Test note for identifier")

        self.go_next_step()

    def complete_assign_to_group_step(self, required_only=False) -> None:
        if required_only:
            self.go_next_step()
            return

        driver = self.driver

        # Click the button to show the add new group dialog
        driver.find_element(By.ID, "show-add-new-group-dialog").click()

        # Wait for the modal to appear
        WebDriverWait(driver, 0.2)

        # Fill out the form in the modal
        group_name_input = driver.find_element(By.ID, "id_submission_group_name")
        group_description_input = driver.find_element(By.ID, "id_submission_group_description")

        group_name_input.send_keys("Test Group")
        group_description_input.send_keys("Test description for group")

        # Submit the form to create the new group
        driver.find_element(By.ID, "id_create_group_button").click()

        # Wait for the modal to close and the new group to be added to the select options
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.NAME, "grouptransfer-group_id"))
        )

        # Check that the new group is selected
        group_select = Select(driver.find_element(By.NAME, "grouptransfer-group_id"))
        selected_option = group_select.first_selected_option
        self.assertEqual(selected_option.text, "Test Group")

        self.go_next_step()

    def test_complete_form_till_review_step(self) -> None:
        self.login()
        driver = self.driver

        # Navigate to the transfer form wizard
        driver.get(f"{self.live_server_url}/transfer/")

        self.complete_legal_agreement_step()
        self.complete_contact_information_step()
        self.complete_source_information_step()
        self.complete_record_description_step()
        self.complete_record_rights_step()
        self.complete_other_identifiers_step()
        self.complete_assign_to_group_step()

    def test_login(self) -> None:
        """Test that the user can log in."""
        self.login()
        # Verify that the user is logged in by checking the presence of a specific element
        self.assertTrue(self.driver.find_element(By.ID, "logout-btn"))

    def test_previous_saves_form(self) -> None:
        """Test that the form data is saved when going to the previous step."""
        self.login()
        driver = self.driver

        # Navigate to the transfer form wizard
        driver.get(f"{self.live_server_url}/transfer/")

        # Fill out the Legal Agreement step
        accept_agreement_checkbox = driver.find_element(By.NAME, "acceptlegal-agreement_accepted")
        accept_agreement_checkbox.click()
        driver.find_element(By.ID, "form-next-button").click()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "contactinfo-contact_name"))
        )

        # Fill out some required fields in the the Contact Information step
        contact_name_input = driver.find_element(By.NAME, "contactinfo-contact_name")
        phone_number_input = driver.find_element(By.NAME, "contactinfo-phone_number")
        email_input = driver.find_element(By.NAME, "contactinfo-email")

        contact_name_input.send_keys("John Doe")
        phone_number_input.send_keys("+1 (999) 999-9999")
        email_input.send_keys("john.doe@example.com")
        driver.find_element(By.ID, "form-previous-button").click()

        # Wait for previous step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "acceptlegal-agreement_accepted"))
        )

        # Verify that the Legal Agreement step is still filled out
        accept_agreement_checkbox = driver.find_element(By.NAME, "acceptlegal-agreement_accepted")
        self.assertTrue(accept_agreement_checkbox.is_selected())

        # Go back to the Contact Information step
        driver.find_element(By.ID, "form-next-button").click()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "contactinfo-contact_name"))
        )

        # Get the Contact Information step inputs
        contact_name_input = driver.find_element(By.NAME, "contactinfo-contact_name")
        phone_number_input = driver.find_element(By.NAME, "contactinfo-phone_number")
        email_input = driver.find_element(By.NAME, "contactinfo-email")

        # Verify that the Contact Information step is still filled out
        self.assertEqual(contact_name_input.get_attribute("value"), "John Doe")
        self.assertEqual(phone_number_input.get_attribute("value"), "+1 (999) 999-9999")
        self.assertEqual(email_input.get_attribute("value"), "john.doe@example.com")

        # Fill out the rest of the Contact Information step
        address_line_1_input = driver.find_element(By.NAME, "contactinfo-address_line_1")
        city_input = driver.find_element(By.NAME, "contactinfo-city")
        province_or_state_input = driver.find_element(By.NAME, "contactinfo-province_or_state")
        postal_or_zip_code_input = driver.find_element(By.NAME, "contactinfo-postal_or_zip_code")
        country_input = driver.find_element(By.NAME, "contactinfo-country")

        address_line_1_input.send_keys("123 Main St")
        city_input.send_keys("Winnipeg")
        province_or_state_input.send_keys("MB")
        postal_or_zip_code_input.send_keys("R3C 1A5")
        country_input.send_keys("CA")

        # Go to the next step
        driver.find_element(By.ID, "form-next-button").click()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "sourceinfo-enter_manual_source_info"))
        )

        # Optional step so go to next step
        driver.find_element(By.ID, "form-next-button").click()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "recorddescription-accession_title"))
        )

        # Fill out some fields in the Record Description step
        accession_title_input = driver.find_element(By.NAME, "recorddescription-accession_title")
        description_input = driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        accession_title_input.send_keys("Test Accession Title")
        description_input.send_keys("Test Description")

        # Go back to the Contact Information step
        driver.find_element(By.ID, "form-previous-button").click()

        # Wait for the previous step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "sourceinfo-enter_manual_source_info"))
        )

        # Verify that the Source Information step is still filled out as expected
        enter_manual_source_info_checkbox = driver.find_element(
            By.NAME, "sourceinfo-enter_manual_source_info"
        )
        self.assertFalse(enter_manual_source_info_checkbox.is_selected())

        # Go back to the Record Description step
        driver.find_element(By.ID, "form-next-button").click()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "recorddescription-accession_title"))
        )

        # Verify that the Record Description step is still filled out as expected
        accession_title_input = driver.find_element(By.NAME, "recorddescription-accession_title")
        description_input = driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        self.assertEqual(accession_title_input.get_attribute("value"), "Test Accession Title")
        self.assertEqual(description_input.get_attribute("value"), "Test Description")
