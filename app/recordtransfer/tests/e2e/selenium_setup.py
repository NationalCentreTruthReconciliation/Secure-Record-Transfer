from abc import ABC

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumLiveServerTestCase(StaticLiveServerTestCase, ABC):
    """Class used to run Selenium-based E2E tests."""

    def setUp(self) -> None:
        """Set up the test case by initializing the web driver."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-autofill")
        chrome_options.add_argument("--disable-save-password-bubble")
        if settings.SELENIUM_TESTS_HEADLESS_MODE:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--guest")

        prefs = {
            "autofill.profile_enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        # Set up the web driver (e.g., Chrome)
        self.driver = webdriver.Chrome(options=chrome_options)

    def tearDown(self) -> None:
        """Tear down the test case by quitting the web driver."""
        self.driver.quit()

    def login(self, username: str, password: str) -> None:
        """Log in the test user."""
        driver = self.driver
        login_url = reverse("login")
        driver.get(f"{self.live_server_url}{login_url}")

        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        username_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "logout-btn")))
