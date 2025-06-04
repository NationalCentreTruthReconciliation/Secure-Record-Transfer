from abc import ABC

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver


class SeleniumLiveServerTestCase(StaticLiveServerTestCase, ABC):
    """Class used to run Selenium-based E2E tests."""

    def setUp(self):
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
