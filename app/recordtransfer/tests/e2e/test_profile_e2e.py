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

        # DEBUG: Check for CSRF token
        csrf_tokens = driver.find_elements(By.CSS_SELECTOR, "input[name='csrfmiddlewaretoken']")
        print(f"CSRF tokens found: {len(csrf_tokens)}")
        for token in csrf_tokens:
            print(f"  CSRF value: {token.get_attribute('value')[:20]}...")

        # DEBUG: Check what form fields exist
        form_inputs = driver.find_elements(By.CSS_SELECTOR, "form input")
        print("Form inputs found:")
        for inp in form_inputs:
            name = inp.get_attribute("name")
            input_type = inp.get_attribute("type")
            print(f"  - {input_type}: name='{name}'")

        # Fill form
        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        # Submit form
        form = driver.find_element(By.TAG_NAME, "form")
        form.submit()
        print("Form submitted directly")

        import time

        time.sleep(3)

        # DEBUG: Check for error messages after submission
        error_elements = driver.find_elements(
            By.CSS_SELECTOR, ".alert, .error, .message, .errorlist"
        )
        print(f"Error/message elements found: {len(error_elements)}")
        for error in error_elements:
            print(f"  Error/Message: '{error.text}'")

        # Check if password fields are cleared (sign of successful submission)
        current_val = driver.find_element(By.NAME, "current_password").get_attribute("value")
        new_val = driver.find_element(By.NAME, "new_password").get_attribute("value")
        confirm_val = driver.find_element(By.NAME, "confirm_new_password").get_attribute("value")

        print(f"Form field values after submission:")
        print(f"  Current password: '{current_val}'")
        print(f"  New password: '{new_val}'")
        print(f"  Confirm password: '{confirm_val}'")

        # Check database
        from django.contrib.auth import authenticate

        old_works = authenticate(username="testuser", password="testpassword")
        new_works = authenticate(username="testuser", password="newsecurepassword")

        print(f"Old password works: {old_works is not None}")
        print(f"New password works: {new_works is not None}")

        if new_works:
            print("SUCCESS: Password was changed!")
        else:
            print("FAILED: Password was not changed")
            print("Check /tmp/profile_before.html and /tmp/profile_after.html")
            self.fail("Password change was not successful")
