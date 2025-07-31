import os

from django.conf import settings
from django.test import override_settings, tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .selenium_setup import SeleniumLiveServerTestCase


@tag("e2e")
@override_settings(
    WEBPACK_LOADER={
        "DEFAULT": {
            "STATS_FILE": os.path.join(
                os.path.dirname(settings.APPLICATION_BASE_DIR), "dist", "webpack-stats.json"
            ),
        },
    }
)
class TestLanguageSwitch(SeleniumLiveServerTestCase):
    """End-to-end tests for verifying that switching the language sets the correct cookie."""

    def test_language_switch_sets_cookie(self) -> None:
        """Switching the language to Hindi sets the language cookie to 'hi'."""
        driver = self.driver
        driver.get(self.live_server_url)

        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "language"))
        )
        Select(lang_dropdown).select_by_value("hi")

        def get_language_cookie(driver: webdriver.Remote):
            cookie = driver.get_cookie(settings.LANGUAGE_COOKIE_NAME)
            if cookie is not None and cookie.get("value") == "hi":
                return cookie
            return None

        language_cookie = WebDriverWait(driver, 10).until(get_language_cookie)
        self.assertIsNotNone(language_cookie)
