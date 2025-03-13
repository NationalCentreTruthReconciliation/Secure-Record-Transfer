import tempfile
from typing import ClassVar

from caais.models import RightsType, SourceRole, SourceType
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from recordtransfer.constants import FORMTITLE
from recordtransfer.enums import SubmissionStep
from recordtransfer.models import User
from recordtransfer.views.pre_submission import SubmissionFormWizard


def get_section_title(step: SubmissionStep) -> str:
    """Get section title for a given step."""
    return SubmissionFormWizard._TEMPLATES[step][FORMTITLE]


@tag("e2e")
class SubmissionFormWizardTest(StaticLiveServerTestCase):
    """End-to-end tests for the submission form wizard."""

    test_data: ClassVar[dict] = {
        SubmissionStep.CONTACT_INFO: {
            "section_title": get_section_title(SubmissionStep.CONTACT_INFO),
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
        SubmissionStep.SOURCE_INFO: {
            "section_title": get_section_title(SubmissionStep.SOURCE_INFO),
            "source_name": "Test Source Name",
            "source_type": "Individual",
            "source_role": "Donor",
            "source_note": "Test Source Note",
            "preliminary_custodial_history": "Test Custodial History",
        },
        SubmissionStep.RECORD_DESCRIPTION: {
            "section_title": get_section_title(SubmissionStep.RECORD_DESCRIPTION),
            "accession_title": "Test Accession Title",
            "date_of_materials": "[ca. 2021-01-01 - 2021-01-31]",
            "language": "English",
            "description": "Test Description",
            "condition": "Test Condition",
        },
        SubmissionStep.RIGHTS: {
            "section_title": get_section_title(SubmissionStep.RIGHTS),
            "rights_type": "Copyright",
            "rights_value": "Copyright until 2050, applies to all files",
        },
        SubmissionStep.OTHER_IDENTIFIERS: {
            "section_title": get_section_title(SubmissionStep.OTHER_IDENTIFIERS),
            "type": "Receipt number",
            "value": "123456",
            "note": "Test note for identifier",
        },
        SubmissionStep.GROUP_SUBMISSION: {
            "section_title": get_section_title(SubmissionStep.GROUP_SUBMISSION),
            "name": "Test Group",
            "description": "Test description for group",
        },
        SubmissionStep.UPLOAD_FILES: {
            "section_title": get_section_title(SubmissionStep.UPLOAD_FILES),
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
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        prefs = {"autofill.profile_enabled": False}
        chrome_options.add_experimental_option("prefs", prefs)

        # Set up the web driver (e.g., Chrome)
        self.driver = webdriver.Chrome(options=chrome_options)

        # Create a test user
        self.setUpTestData()

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.user = User.objects.create_user(username="testuser", password="testpassword")

        ### This section restores the database to the state after migrations ###

        # Create rights types
        for name, description in (
            ("Other", "A type of rights not listed elsewhere"),
            ("Unknown", "Use when it is not known what type of rights pertain to the material"),
            ("Cultural Rights", "Accss to material is limited according to cultural protocols"),
            ("Statute", "Access to material is limited according to law or legislation"),
            ("License", "Access to material is limited by a licensing agreement"),
            (
                "Access",
                "Access to material is restricted to a certain entity or group of entities",
            ),
            (
                "Copyright",
                "Access to material is based on fair dealing OR material is in the public domain",
            ),
        ):
            rights_type, created = RightsType.objects.get_or_create(
                name=name,
                description=description,
            )
            if created:
                rights_type.save()

        # Create Source Information types
        other_type, created = SourceType.objects.get_or_create(
            name="Other",
            description="Placeholder right to allow user to specify unique source type",
        )
        if created:
            other_type.save()

        other_role, created = SourceRole.objects.get_or_create(
            name="Other",
            description="Placeholder right to allow user to specify unique source role",
        )
        if created:
            other_role.save()

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
        """Go to the next step in the form."""
        driver = self.driver
        driver.find_element(By.ID, "form-next-button").click()

    def go_previous_step(self) -> None:
        """Go to the previous step in the form."""
        driver = self.driver
        driver.find_element(By.ID, "form-previous-button").click()

    def go_to_review_step(self) -> None:
        """Go to the review step in the form."""
        driver = self.driver
        driver.find_element(By.ID, "form-review-button").click()

    def complete_legal_agreement_step(self) -> None:
        """Complete the Legal Agreement step."""
        driver = self.driver

        # Complete the Legal Agreement step
        accept_agreement_checkbox = driver.find_element(By.NAME, "acceptlegal-agreement_accepted")
        accept_agreement_checkbox.click()
        driver.find_element(By.ID, "form-next-button").click()

    def complete_contact_information_step(self, required_only: bool = False) -> None:
        """Complete the Contact Information step."""
        driver = self.driver
        data = self.test_data[SubmissionStep.CONTACT_INFO]

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
        """Complete the Source Information step. Opts for the option of submitting on behalf of an
        organization/another person.
        """
        driver = self.driver
        data = self.test_data[SubmissionStep.SOURCE_INFO]

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
        source_type_select.select_by_visible_text(data["source_type"])
        source_role_select.select_by_visible_text(data["source_role"])

        if not required_only:
            source_note_input = driver.find_element(By.NAME, "sourceinfo-source_note")
            preliminary_custodial_history = driver.find_element(
                By.NAME, "sourceinfo-preliminary_custodial_history"
            )

            source_note_input.send_keys(data["source_note"])
            preliminary_custodial_history.send_keys(data["preliminary_custodial_history"])

        self.go_next_step()

    def complete_record_description_step(self, required_only: bool = False) -> None:
        """Complete the Record Description step."""
        driver = self.driver
        data = self.test_data[SubmissionStep.RECORD_DESCRIPTION]

        accession_title_input = driver.find_element(By.NAME, "recorddescription-accession_title")
        date_input = driver.find_element(By.NAME, "recorddescription-date_of_materials")
        approx_date_input = driver.find_element(By.NAME, "recorddescription-date_is_approximate")
        language_input = driver.find_element(By.NAME, "recorddescription-language_of_material")
        description_of_contents_input = driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        accession_title_input.send_keys(data["accession_title"])

        # Click on date input field
        date_input.click()

        # Click on the datepicker title to open year/month selection view
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "air-datepicker-nav--title"))
        ).click()

        # Click on year selection title
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "air-datepicker-nav--title"))
        ).click()

        # Click on the year 2021
        driver.find_element(
            By.XPATH, "//div[@data-year='2021' and @data-month='0' and @data-date='1']"
        ).click()

        # Click on the month January
        driver.find_element(
            By.XPATH,
            "//div[@data-year='2021' and @data-month='0' and @data-date='1' and contains(@class, 'air-datepicker-cell -month-')]",
        ).click()

        # Click on the date 1
        driver.find_element(
            By.XPATH,
            "//div[@data-year='2021' and @data-month='0' and @data-date='1' and contains(@class, 'air-datepicker-cell -day-')]",
        ).click()

        # Click on the date 31
        driver.find_element(
            By.XPATH,
            "//div[@data-year='2021' and @data-month='0' and @data-date='31' and contains(@class, 'air-datepicker-cell -day-')]",
        ).click()

        # Click checkbox to mark date as approximate
        approx_date_input.click()

        language_input.send_keys(data["language"])
        description_of_contents_input.send_keys(data["description"])

        if not required_only:
            condition_input = driver.find_element(
                By.NAME, "recorddescription-condition_assessment"
            )

            condition_input.send_keys(data["condition"])

        self.go_next_step()

    def complete_record_rights_step(self, required_only: bool = False) -> None:
        """Complete the Record Rights step."""
        driver = self.driver
        data = self.test_data[SubmissionStep.RIGHTS]

        rights_type_select = Select(driver.find_element(By.NAME, "rights-0-rights_type"))
        rights_type_select.select_by_visible_text(data["rights_type"])

        if not required_only:
            rights_value_textarea = driver.find_element(By.NAME, "rights-0-rights_value")
            rights_value_textarea.send_keys(data["rights_value"])

        self.go_next_step()

    def complete_other_identifiers_step(self, required_only: bool = False) -> None:
        """Complete the Other Identifiers step."""
        if required_only:
            self.go_next_step()
            return

        driver = self.driver
        data = self.test_data[SubmissionStep.OTHER_IDENTIFIERS]

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

    def complete_assign_to_group_step(self, required_only: bool = False) -> None:
        """Complete the Assign to Group step."""
        if required_only:
            self.go_next_step()
            return

        driver = self.driver
        data = self.test_data[SubmissionStep.GROUP_SUBMISSION]

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
            EC.invisibility_of_element_located((By.ID, "id_create_group_button"))
        )

        # Check that the new group is selected
        group_select = Select(driver.find_element(By.NAME, "groupsubmission-group_uuid"))
        selected_option = group_select.first_selected_option
        self.assertEqual(selected_option.text, data["name"])

        self.go_next_step()

    def upload_files_step(self, required_only: bool = False) -> None:
        """Complete the Upload Files step."""
        data = self.test_data[SubmissionStep.UPLOAD_FILES]

        # Create temp file with specified name
        with tempfile.NamedTemporaryFile(suffix=data["filename"]) as temp_file:
            temp_file.write(data["content"])
            temp_file.flush()
            temp_path = temp_file.name

            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(temp_path)

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "is-complete"))
            )

            if not required_only:
                general_note_input = self.driver.find_element(By.NAME, "uploadfiles-general_note")
                general_note_input.send_keys(data["general_note"])

            self.go_to_review_step()

    def complete_form_till_review_step(self) -> None:
        """Complete the form till the review step."""
        self.login()
        driver = self.driver

        # Navigate to the submission form wizard
        driver.get(f"{self.live_server_url}/submission/new/")

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

    def test_review_step(self) -> None:
        """Verify that the displayed information on the review page matches the test data."""
        self.complete_form_till_review_step()
        driver = self.driver

        # Wait for the review step to load
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "review-summary"))
        )

        # Verify section titles and content for each step
        for step, data in self.test_data.items():
            section_title = driver.find_element(
                By.XPATH,
                f"//h2[contains(@class, 'section-title') and contains(text(), '{data['section_title']}')]",
            )
            self.assertTrue(section_title.is_displayed())

            # Check specific fields based on step
            if step == SubmissionStep.CONTACT_INFO:
                fields = {
                    "Contact name": data["contact_name"],
                    "Phone number": data["phone_number"],
                    "Email": data["email"],
                    "Address line 1": data["address_line_1"],
                    "City": data["city"],
                    "Province or state": data["province_or_state"],
                    "Postal / Zip code": data["postal_or_zip_code"],
                    "Country": data["country"],
                    "Job title": data["job_title"],
                    "Organization": data["organization"],
                }
                self._verify_field_values("contactinfo", fields)

            elif step == SubmissionStep.SOURCE_INFO:
                fields = {
                    "Name of source": data["source_name"],
                    "Source type": "Individual",
                    "Source role": "Donor",
                    "Source notes": data["source_note"],
                    "Custodial history": data["preliminary_custodial_history"],
                }
                self._verify_field_values("sourceinfo", fields)

            elif step == SubmissionStep.RECORD_DESCRIPTION:
                fields = {
                    "Title": data["accession_title"],
                    "Language(s)": data["language"],
                    "Date of materials": data["date_of_materials"],
                    "Description of contents": data["description"],
                    "Condition of files": data["condition"],
                }
                self._verify_field_values("recorddescription", fields)

            elif step == SubmissionStep.RIGHTS:
                rights_type = driver.find_element(
                    By.XPATH, "//dt[text()='Type of rights']/following-sibling::dd[1]"
                )
                rights_value = driver.find_element(
                    By.XPATH, "//dt[text()='Notes for rights']/following-sibling::dd[1]"
                )
                self.assertEqual(rights_type.text, "Copyright")
                self.assertEqual(rights_value.text, data["rights_value"])

            elif step == SubmissionStep.OTHER_IDENTIFIERS:
                identifier_fields = {
                    "Type of identifier": data["type"],
                    "Identifier value": data["value"],
                    "Notes for identifier": data["note"],
                }
                self._verify_field_values("otheridentifiers", identifier_fields)

            elif step == SubmissionStep.GROUP_SUBMISSION:
                group_name = driver.find_element(
                    By.XPATH, "//dt[text()='Assigned group']/following-sibling::dd[1]"
                )
                self.assertEqual(group_name.text, data["name"])

            elif step == SubmissionStep.UPLOAD_FILES:
                # Verify file upload
                file_element = driver.find_element(By.CLASS_NAME, "file-entry")
                self.assertTrue(file_element.is_displayed())
                self.assertTrue(data["filename"] in file_element.text)

                if data["general_note"]:
                    note_element = driver.find_element(
                        By.XPATH, "//dt[text()='Other notes']/following-sibling::dd[1]"
                    )
                    self.assertEqual(note_element.text, data["general_note"])

    def _verify_field_values(self, section_id: str, fields: dict) -> None:
        """Verify field values in a section."""
        for label, expected_value in fields.items():
            if expected_value:  # Only check non-empty values
                xpath = f"//dt[text()='{label}']/following-sibling::dd[1]"
                element = self.driver.find_element(By.XPATH, xpath)
                self.assertEqual(element.text, expected_value)

    def test_previous_saves_form(self) -> None:
        """Test that the form data is saved when going to the previous step. Uses the Contact
        Information step and the Record Description step as test cases.
        """
        self.login()
        driver = self.driver

        # Navigate to the submission form wizard
        driver.get(f"{self.live_server_url}/submission/new")

        # Fill out the Legal Agreement step
        self.complete_legal_agreement_step()

        # Fill out some required fields in the Contact Information step
        data = self.test_data[SubmissionStep.CONTACT_INFO]

        # Wait for Contact Information step to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "contactinfo-contact_name"))
        )

        contact_name_input = driver.find_element(By.NAME, "contactinfo-contact_name")
        phone_number_input = driver.find_element(By.NAME, "contactinfo-phone_number")
        email_input = driver.find_element(By.NAME, "contactinfo-email")

        contact_name_input.send_keys(data["contact_name"])
        phone_number_input.send_keys(data["phone_number"])
        email_input.send_keys(data["email"])
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

        # Re-find the elements after navigating back to the Contact Information step
        contact_name_input = driver.find_element(By.NAME, "contactinfo-contact_name")
        phone_number_input = driver.find_element(By.NAME, "contactinfo-phone_number")
        email_input = driver.find_element(By.NAME, "contactinfo-email")

        # Verify that the Contact Information step is still filled out
        self.assertEqual(contact_name_input.get_attribute("value"), data["contact_name"])
        self.assertEqual(phone_number_input.get_attribute("value"), data["phone_number"])
        self.assertEqual(email_input.get_attribute("value"), data["email"])

        # Fill out the rest of the Contact Information step
        address_line_1_input = driver.find_element(By.NAME, "contactinfo-address_line_1")
        city_input = driver.find_element(By.NAME, "contactinfo-city")
        province_or_state_input = driver.find_element(By.NAME, "contactinfo-province_or_state")
        postal_or_zip_code_input = driver.find_element(By.NAME, "contactinfo-postal_or_zip_code")
        country_input = driver.find_element(By.NAME, "contactinfo-country")

        address_line_1_input.send_keys(data["address_line_1"])
        city_input.send_keys(data["city"])
        province_or_state_input.send_keys(data["province_or_state"])
        postal_or_zip_code_input.send_keys(data["postal_or_zip_code"])
        country_input.send_keys(data["country"])

        # Go to Source Information step
        self.go_next_step()

        # Wait for the next step to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "sourceinfo-enter_manual_source_info"))
        )

        # Optional step so go to next step
        self.go_next_step()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "recorddescription-accession_title"))
        )

        # Fill out some fields in the Record Description step
        data = self.test_data[SubmissionStep.RECORD_DESCRIPTION]
        accession_title_input = driver.find_element(By.NAME, "recorddescription-accession_title")
        description_input = driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        accession_title_input.send_keys(data["accession_title"])
        description_input.send_keys(data["description"])

        # Go back to the Contact Information step
        self.go_previous_step()

        # Wait for the previous step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "sourceinfo-enter_manual_source_info"))
        )

        # Go back to the Record Description step
        self.go_next_step()

        # Wait for the next step to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "recorddescription-accession_title"))
        )

        # Refind the elements after navigating back to the Record Description step
        accession_title_input = driver.find_element(By.NAME, "recorddescription-accession_title")
        description_input = driver.find_element(
            By.NAME, "recorddescription-preliminary_scope_and_content"
        )

        # Verify that the Record Description step is still filled out
        self.assertEqual(accession_title_input.get_attribute("value"), data["accession_title"])
        self.assertEqual(description_input.get_attribute("value"), data["description"])
