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

        # Fill form
        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        # Find the form and submit it directly
        form = driver.find_element(By.TAG_NAME, "form")
        form.submit()
        print("Form submitted directly")
        # Check if password fields are empty
        # Check for success message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-error"))
        )

        # Get the error message text
        error_alert = driver.find_element(By.CLASS_NAME, "alert-error")
        error_message = error_alert.text
        print(f"ERROR FOUND: {error_message}")

        # Also check for other error elements
        all_errors = driver.find_elements(
            By.CSS_SELECTOR, ".error, .alert-error, .invalid-feedback, .errorlist"
        )
        print(f"Found {len(all_errors)} error elements:")
        for i, error in enumerate(all_errors):
            print(f"  Error {i}: {error.text}")

        # Save page source for debugging
        with open("/tmp/profile_error_debug.html", "w") as f:
            f.write(driver.page_source)
        print("Page source with errors saved to /tmp/profile_error_debug.html")

        # The test should fail here so we can see what the error is
        self.fail(f"Form submission failed with error: {error_message}")
