from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from recordtransfer.models import User


class TransferFormWizardTest(LiveServerTestCase):
    def setUp(self):
        # Set up Chrome options to disable autofill
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-autofill")
        chrome_options.add_argument("--disable-save-password-bubble")
        prefs = {
            'autofill.profile_enabled': False
        }
        chrome_options.add_experimental_option('prefs', prefs)

        # Set up the web driver (e.g., Chrome)
        self.driver = webdriver.Chrome(options=chrome_options)

        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def tearDown(self):
        # Close the web driver
        self.driver.quit()

    def login(self):
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

    def test_login(self):
        self.login()
        # Verify that the user is logged in by checking the presence of a specific element
        self.assertTrue(self.driver.find_element(By.ID, "logout-btn"))

    def test_previous_saves_form(self):
        self.login()
        driver = self.driver

        # Navigate to the transfer form wizard
        driver.get(f"{self.live_server_url}/transfer/")

        # Fill out the Legal Agreement step
        accept_agreement_checkbox = driver.find_element(By.NAME, "acceptlegal-agreement_accepted")
        accept_agreement_checkbox.click()
        driver.find_element(By.ID, "form-next-button").click()

        # Wait for the next step to load
        WebDriverWait(driver, 60).until(
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
