from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from recordtransfer.models import User


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
            username="testuser", email="testuser@example.com", password="testpassword"
        )

    def tearDown(self):
        self.driver.quit()

    def login(self) -> None:
        """Log in the test user."""
        driver = self.driver
        login_url = reverse("login")
        # Open the login page
        driver.get(f"{self.live_server_url}{login_url}")

        # Log in
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys("testuser")
        password_input.send_keys("testpassword")
        password_input.send_keys(Keys.RETURN)

        # Wait for the login to complete and redirect to the home page
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "logout-btn")))

    def test_reset_password_from_profile(self):
        driver = self.driver
        self.login()

        # Step 1: Navigate to profile page
        driver.get(f"{self.live_server_url}/user/profile/")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

        # Step 2: Fill in the change password form
        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        # DEBUG: Check if button is present and enabled
        save_button = driver.find_element(By.ID, "id_save_button")
        print(f"Save button found: {save_button.is_enabled()}")
        print(f"Save button text: {save_button.text}")

        # Step 3: Submit the form
        save_button.click()

        # DEBUG: Wait a moment and check what happened
        import time

        time.sleep(3)

        print(f"Current URL after submission: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Look for any alert/message elements
        alerts = driver.find_elements(By.CSS_SELECTOR, ".alert, .message, .success, .error")
        print(f"Found {len(alerts)} alert elements:")
        for alert in alerts:
            print(f"  - Class: {alert.get_attribute('class')}, Text: {alert.text}")

        # Check if there are form errors
        errors = driver.find_elements(By.CSS_SELECTOR, ".error, .invalid-feedback, .form-error")
        print(f"Found {len(errors)} error elements:")
        for error in errors:
            print(f"  - Error: {error.text}")

        # Step 4: Try multiple success indicators
        try:
            WebDriverWait(driver, 5).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "alert-success")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".alert")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".message")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".success")),
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "success"),
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "updated"),
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "changed"),
                )
            )
            print("SUCCESS: Found success indicator")
        except Exception as e:
            print(f"FAILED: No success indicator found: {e}")

            # Save page source for debugging
            with open("/tmp/profile_after_submit.html", "w") as f:
                f.write(driver.page_source)
            print("Page source saved to /tmp/profile_after_submit.html")
            raise
