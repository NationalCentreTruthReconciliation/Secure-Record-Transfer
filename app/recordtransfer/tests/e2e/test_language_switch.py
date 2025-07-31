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
        """Test that switching the language sets the 'django_language' cookie to the
        selected value.
        """
        driver = self.driver

        # Wait for the language dropdown to be present
        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "language"))
        )
        Select(lang_dropdown).select_by_value("hi")

        # Wait for the cookie to be set (language switch may be async)
        def cookie_is_hi(driver: webdriver.Chrome) -> bool:
            cookie = driver.get_cookie("django_language")
            return cookie is not None and cookie.get("value") == "hi"

        WebDriverWait(driver, 10).until(cookie_is_hi)
        language_cookie = driver.get_cookie("django_language")
        assert language_cookie is not None, "django_language cookie was not set"
        assert language_cookie["value"] == "hi"
