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

        # DEBUG: Save the page before doing anything
        with open("/tmp/profile_before.html", "w") as f:
            f.write(driver.page_source)
        print("Page saved before form submission")

        # Fill form
        driver.find_element(By.NAME, "current_password").send_keys("testpassword")
        driver.find_element(By.NAME, "new_password").send_keys("newsecurepassword")
        driver.find_element(By.NAME, "confirm_new_password").send_keys("newsecurepassword")

        # DEBUG: Check current URL and form action
        print(f"Current URL: {driver.current_url}")

        form = driver.find_element(By.TAG_NAME, "form")
        form_action = form.get_attribute("action")
        form_method = form.get_attribute("method")
        print(f"Form action: '{form_action}'")
        print(f"Form method: '{form_method}'")

        # Just submit the form directly
        form.submit()
        print("Form submitted directly")

        # Wait and check what happened
        import time

        time.sleep(3)

        # DEBUG: Save page after submission
        with open("/tmp/profile_after.html", "w") as f:
            f.write(driver.page_source)
        print("Page saved after form submission")

        # Check URL after submission
        print(f"URL after submission: {driver.current_url}")

        # Check if password actually changed in database
        from django.contrib.auth import authenticate

        old_works = authenticate(username="testuser", password="testpassword")
        new_works = authenticate(username="testuser", password="newsecurepassword")

        print(f"Old password works: {old_works is not None}")
        print(f"New password works: {new_works is not None}")

        # Don't assert yet - just print results
        if new_works:
            print("SUCCESS: Password was changed!")
        else:
            print("FAILED: Password was not changed")
            print("Check /tmp/profile_before.html and /tmp/profile_after.html")
