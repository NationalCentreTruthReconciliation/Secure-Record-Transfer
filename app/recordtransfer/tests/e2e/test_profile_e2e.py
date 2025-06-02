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

        driver.get(f"{self.live_server_url}/user/profile/")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "current_password"))
        )

        # Fill and submit form
        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        driver.find_element(By.ID, "id_save_button").click()

        # Wait for processing
        import time

        time.sleep(2)

        # Check if the password was actually changed by testing it in the database
        from django.contrib.auth import authenticate

        # Test if new password works
        user = authenticate(username="testuser", password="newsecurepassword")

        if user is not None:
            print("SUCCESS: Password was changed successfully in database")
        else:
            print("FAILED: Password was not changed")

            # Check for validation errors on the page
            error_elements = driver.find_elements(
                By.CSS_SELECTOR, ".error, .invalid-feedback, .alert-danger, .errorlist"
            )
            if error_elements:
                print("Found validation errors:")
                for error in error_elements:
                    print(f"  - {error.text}")

            # Check current field values
            current_val = driver.find_element(By.NAME, "current_password").get_attribute("value")
            new_val = driver.find_element(By.NAME, "new_password").get_attribute("value")
            confirm_val = driver.find_element(By.NAME, "confirm_new_password").get_attribute(
                "value"
            )

            print(f"Current password field: '{current_val}'")
            print(f"New password field: '{new_val}'")
            print(f"Confirm password field: '{confirm_val}'")

            # Save page source for debugging
            with open("/tmp/profile_debug.html", "w") as f:
                f.write(driver.page_source)
            print("Page source saved to /tmp/profile_debug.html")

            raise AssertionError("Password change failed")
