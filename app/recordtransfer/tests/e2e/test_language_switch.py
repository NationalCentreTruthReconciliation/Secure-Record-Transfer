import os

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from recordtransfer.models import User

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

    def setUp(self) -> None:
        """Set up test data and log in the test user."""
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
            language="en",
        )
        self.login("testuser", "testpassword")

    def test_language_switch_sets_cookie_when_logged_out(self) -> None:
        """Switching the language from the navbar to Hindi sets the language cookie to 'hi'."""
        driver = self.driver

        self.client.logout()
        driver.get(self.live_server_url)

        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "language-switcher"))
        )
        Select(lang_dropdown).select_by_value("hi")

        def get_language_cookie(driver: webdriver.Remote):
            cookie = driver.get_cookie(settings.LANGUAGE_COOKIE_NAME)
            if cookie is not None and cookie.get("value") == "hi":
                return cookie
            return None

        language_cookie = WebDriverWait(driver, 10).until(get_language_cookie)
        self.assertIsNotNone(language_cookie)

    def test_user_preferred_language_used_after_login(self) -> None:
        """When a user logs in, their preferred language saved to their profile is set as the
        cookie, regardless of the language set in the navbar while logged out.
        """
        driver = self.driver
        driver.get(self.live_server_url)

        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "language-switcher"))
        )
        Select(lang_dropdown).select_by_value("fr")

        # Log the user out
        driver.find_element(By.ID, "logout-btn").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "nav-login")))

        # Go to homepage
        driver.get(self.live_server_url)

        # Change language to English while logged out
        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "language-switcher"))
        )
        Select(lang_dropdown).select_by_value("en")

        # Log in again
        self.login("testuser", "testpassword")

        # Check that the language cookie is set to French
        language_cookie = WebDriverWait(driver, 10).until(
            lambda d: d.get_cookie(settings.LANGUAGE_COOKIE_NAME)
        )
        self.assertIsNotNone(language_cookie)
        self.assertEqual(language_cookie.get("value"), "fr")

    def test_same_language_shown_in_navbar_and_profile(self) -> None:
        """Verify that the language shown in the navbar matches the user's preferred language."""
        driver = self.driver
        driver.get(self.live_server_url)

        # Check that the language dropdown shows the user's preferred language
        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "language-switcher"))
        )
        self.assertEqual(Select(lang_dropdown).first_selected_option.get_attribute("value"), "en")

        # Go to the profile page
        profile_url = reverse("recordtransfer:user_profile")
        driver.get(f"{self.live_server_url}{profile_url}")

        # Switch to language tab
        language_radio = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_language_tab"))
        )
        language_radio.click()

        # Check that the language dropdown shows the user's preferred language
        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "profile-language-switcher"))
        )
        self.assertEqual(Select(lang_dropdown).first_selected_option.get_attribute("value"), "en")

        # Change the language to French from profile
        Select(lang_dropdown).select_by_value("fr")

        # Wait for page to reload, and check that the navbar selected language is now French
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "language-switcher").get_attribute("value") == "fr"
        )

        # Change the language back to Hindi from the navbar this time
        lang_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "language-switcher"))
        )
        Select(lang_dropdown).select_by_value("hi")

        # Wait for page to reload, and check that the profile selected language is now Hindi
        language_radio = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "id_language_tab"))
        )
        language_radio.click()
        WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.ID, "profile-language-switcher").get_attribute("value")
            == "hi"
        )
