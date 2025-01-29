import os
import tempfile
from typing import ClassVar

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from recordtransfer.models import User


class TransferFormWizardTest(StaticLiveServerTestCase):
    """End-to-end tests for the transfer form wizard."""

    test_data: ClassVar[dict] = {
        "contact_info": {
            "contact_name": "John Doe",
            "phone_number": "+1 (999) 999-9999",
            "email": "john.doe@example.com",
            "address_line_1": "123 Main St",
            "city": "Winnipeg",
            "province_or_state": "MB",
            "postal_or_zip_code": "R3C 1A5",
            "country": "CA",
            "job_title": "Archivist",
            "organization": "Test Organization",
        },
        "source_info": {
            "source_name": "Test Source Name",
            "source_type": "2",  # Individual
            "source_role": "2",  # Donor
            "source_note": "Test Source Note",
            "preliminary_custodial_history": "Test Custodial History",
        },
        "record_description": {
            "accession_title": "Test Accession Title",
            "start_date": "2021-01-01",
            "end_date": "2021-12-31",
            "language": "English",
            "description": "Test Description",
            "condition": "Test Condition",
        },
        "record_rights": {
            "rights_type": "7",  # Copyright
            "rights_value": "Copyright until 2050, applies to all files",
        },
        "other_identifiers": {
            "type": "Receipt number",
            "value": "123456",
            "note": "Test note for identifier",
        },
        "group": {"name": "Test Group", "description": "Test description for group"},
        "upload_files": {
            "general_note": "Test general note",
            "filename": "test_upload.txt",
            "content": b"Test content" * 512,  # 5 KB
        },
    }

    def setUp(self) -> None:
        """Set up the web driver and create a test user."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-autofill")
        chrome_options.add_argument("--disable-save-password-bubble")
        chrome_options.add_argument("--headless")
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

    def go_to_review_step(self) -> None:
        driver = self.driver
        driver.find_element(By.ID, "form-review-button").click()

    def complete_legal_agreement_step(self) -> None:
        driver = self.driver

        # Complete the Legal Agreement step
        accept_agreement_checkbox = driver.find_element(By.NAME, "acceptlegal-agreement_accepted")
        accept_agreement_checkbox.click()
        driver.find_element(By.ID, "form-next-button").click()

    def complete_contact_information_step(self, required_only: bool = False) -> None:
        driver = self.driver
        data = self.test_data["contact_info"]

        # Complete the Contact Information step
        contact_name_input = driver.find_element(By.NAME, "contactinfo-contact_name")
        phone_number_input = driver.find_element(By.NAME, "contactinfo-phone_number")
        email_input = driver.find_element(By.NAME, "contactinfo-email")
        address_line_1_input = driver.find_element(By.NAME, "contactinfo-address_line_1")
        city_input = driver.find_element(By.NAME, "contactinfo-city")
        province_or_state_input = driver.find_element(By.NAME, "contactinfo-province_or_state")
        postal_or_zip_code_input = driver.find_element(By.NAME, "contactinfo-postal_or_zip_code")
        country_input = driver.find_element(By.NAME, "contactinfo-country")

        contact_name_input.send_keys(data["contact_name"])
        phone_number_input.send_keys(data["phone_number"])
        email_input.send_keys(data["email"])
        address_line_1_input.send_keys(data["address_line_1"])
        city_input.send_keys(data["city"])
        province_or_state_input.send_keys(data["province_or_state"])
        postal_or_zip_code_input.send_keys(data["postal_or_zip_code"])
        country_input.send_keys(data["country"])

        if not required_only:
            job_title_input = driver.find_element(By.NAME, "contactinfo-job_title")
            organization_input = driver.find_element(By.NAME, "contactinfo-organization")

            job_title_input.send_keys(data["job_title"])
            organization_input.send_keys(data["organization"])

        self.go_next_step()

    def complete_source_information_step(self, required_only: bool = False) -> None:
        driver = self.driver
        data = self.test_data["source_info"]

        # Complete the Source Information step
        enter_manual_source_info_radio_0 = driver.find_element(
            By.NAME, "sourceinfo-enter_manual_source_info"
        )
        # Click yes
        enter_manual_source_info_radio_0.click()

        source_name_input = driver.find_element(By.NAME, "sourceinfo-source_name")
        source_type_select = Select(driver.find_element(By.NAME, "sourceinfo-source_type"))
        source_role_select = Select(driver.find_element(By.NAME, "sourceinfo-source_role"))

        source_name_input.send_keys(data["source_name"])
        source_type_select.select_by_value(data["source_type"])
        source_role_select.select_by_value(data["source_role"])

        if not required_only:
            source_note_input = driver.find_element(By.NAME, "sourceinfo-source_note")
            preliminary_custodial_history = driver.find_element(
                By.NAME, "sourceinfo-preliminary_custodial_history"
            )

            source_note_input.send_keys(data["source_note"])
            preliminary_custodial_history.send_keys(data["preliminary_custodial_history"])

        self.go_next_step()

    def complete_record_description_step(self, required_only: bool = False) -> None:
        driver = self.driver
        data = self.test_data["record_description"]

        accession_title_input = driver.find_element(By.NAME, "recorddescription-accession_title")
        start_date_input = driver.find_element(By.NAME, "recorddescription-start_date_of_material")
        end_date_input = driver.find_element(By.NAME, "recorddescription-end_date_of_material")
        language_input = driver.find_element(By.NAME, "recorddescription-language_of_material")
        description_of_contents_input = driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        accession_title_input.send_keys(data["accession_title"])
        start_date_input.send_keys(data["start_date"])
        end_date_input.send_keys(data["end_date"])
        language_input.send_keys(data["language"])
        description_of_contents_input.send_keys(data["description"])

        if not required_only:
            condition_input = driver.find_element(
                By.NAME, "recorddescription-condition_assessment"
            )

            condition_input.send_keys(data["condition"])

        self.go_next_step()

    def complete_record_rights_step(self, required_only: bool = False) -> None:
        driver = self.driver
        data = self.test_data["record_rights"]

        # Complete the Record Rights step
        rights_type_select = Select(driver.find_element(By.NAME, "rights-0-rights_type"))

        rights_type_select.select_by_value(data["rights_type"])

        rights_type_select.select_by_value("7")  # Select "Copyright"
        if not required_only:
            rights_value_textarea = driver.find_element(By.NAME, "rights-0-rights_value")
            rights_value_textarea.send_keys(data["rights_value"])

        self.go_next_step()

    def complete_other_identifiers_step(self, required_only: bool = False) -> None:
        if required_only:
            self.go_next_step()
            return

        driver = self.driver
        data = self.test_data["other_identifiers"]

        # Complete the Other Identifiers step
        identifier_type_input = driver.find_element(
            By.NAME, "otheridentifiers-0-other_identifier_type"
        )
        identifier_value_input = driver.find_element(
            By.NAME, "otheridentifiers-0-other_identifier_value"
        )
        identifier_note_input = driver.find_element(
            By.NAME, "otheridentifiers-0-other_identifier_note"
        )

        identifier_type_input.send_keys(data["type"])
        identifier_value_input.send_keys(data["value"])
        identifier_note_input.send_keys(data["note"])

        self.go_next_step()

    def complete_assign_to_group_step(self, required_only=False) -> None:
        if required_only:
            self.go_next_step()
            return

        driver = self.driver
        data = self.test_data["group"]

        # Click the button to show the add new group dialog
        driver.find_element(By.ID, "show-add-new-group-dialog").click()

        # Wait for the modal to appear
        WebDriverWait(driver, 2)

        # Fill out the form in the modal
        group_name_input = driver.find_element(By.ID, "id_submission_group_name")
        group_description_input = driver.find_element(By.ID, "id_submission_group_description")

        group_name_input.send_keys(data["name"])
        group_description_input.send_keys(data["description"])

        # Submit the form to create the new group
        driver.find_element(By.ID, "id_create_group_button").click()

        # Wait for the modal to close and the new group to be added to the select options
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.NAME, "grouptransfer-group_id"))
        )

        # Check that the new group is selected
        group_select = Select(driver.find_element(By.NAME, "grouptransfer-group_id"))
        selected_option = group_select.first_selected_option
        self.assertEqual(selected_option.text, data["name"])

        self.go_next_step()

    def upload_files_step(self, required_only=False):
        data = self.test_data["upload_files"]

        # Create temp file with specified name
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, data["filename"])

        try:
            with open(temp_path, "wb") as temp_file:
                temp_file.write(data["content"])

            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(temp_path)

            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "uppy-Dashboard-Item"))
            )

            if not required_only:
                general_note_input = self.driver.find_element(By.NAME, "uploadfiles-general_note")
                general_note_input.send_keys(data["general_note"])

            self.go_to_review_step()
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

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
        self.upload_files_step()

    def test_login(self) -> None:
        """Test that the user can log in."""
        self.login()
        # Verify that the user is logged in by checking the presence of a specific element
        self.assertTrue(self.driver.find_element(By.ID, "logout-btn"))

    # def test_review_step(self) -> None:
    #     self.complete_form_till_review_step()

    #     # Verify that the review summary shows the correct information
    #     review_summary = self.driver.find_element(By.CLASS_NAME, "review-summary")

    #     # Contact Information
    #     contact_info_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Contact Information']/following-sibling::div"
    #     )
    #     self.assertIn("John Doe", contact_info_section.text)
    #     self.assertIn("+1 (999) 999-9999", contact_info_section.text)
    #     self.assertIn("john.doe@example.com", contact_info_section.text)
    #     self.assertIn("123 Main St", contact_info_section.text)
    #     self.assertIn("Winnipeg", contact_info_section.text)
    #     self.assertIn("MB", contact_info_section.text)
    #     self.assertIn("R3C 1A5", contact_info_section.text)
    #     self.assertIn("CA", contact_info_section.text)

    #     # Source Information
    #     source_info_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Source Information (Optional)']/following-sibling::div"
    #     )
    #     self.assertIn("Test Source Name", source_info_section.text)
    #     self.assertIn("Individual", source_info_section.text)
    #     self.assertIn("Donor", source_info_section.text)

    #     # Record Description
    #     record_description_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Record Description']/following-sibling::div"
    #     )
    #     self.assertIn("Test Accession Title", record_description_section.text)
    #     self.assertIn("2021-01-01", record_description_section.text)
    #     self.assertIn("2021-12-31", record_description_section.text)
    #     self.assertIn("English", record_description_section.text)
    #     self.assertIn("Test Description", record_description_section.text)

    #     # Record Rights
    #     record_rights_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Record Rights']/following-sibling::div"
    #     )
    #     self.assertIn("Copyright", record_rights_section.text)
    #     self.assertIn("Copyright until 2050, applies to all files", record_rights_section.text)

    #     # Other Identifiers
    #     other_identifiers_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Other Identifiers (Optional)']/following-sibling::div"
    #     )
    #     self.assertIn("Receipt number", other_identifiers_section.text)
    #     self.assertIn("123456", other_identifiers_section.text)
    #     self.assertIn("Test note for identifier", other_identifiers_section.text)

    #     # Assign Transfer to Group
    #     group_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Assign Transfer to Group (Optional)']/following-sibling::div"
    #     )
    #     self.assertIn("Test Group", group_section.text)

    #     # Upload Files
    #     upload_files_section = review_summary.find_element(
    #         By.XPATH, "//h2[text()='Upload Files']/following-sibling::div"
    #     )
    #     self.assertIn("test_upload.txt", upload_files_section.text)
    #     self.assertIn("Test general note", upload_files_section.text)

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
