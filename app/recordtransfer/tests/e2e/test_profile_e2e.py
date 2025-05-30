import pytest
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.urls import reverse
from playwright.sync_api import Page, expect, sync_playwright

from recordtransfer.models import User


@tag("e2e")
class ProfilePageTest(StaticLiveServerTestCase):
    """End-to-end tests for the profile page."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create the playwright instance and start the browser."""
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        # TODO: Change setting to more generic name
        if settings.SELENIUM_TESTS_HEADLESS_MODE:
            cls.browser = cls.playwright.chromium.launch(headless=True)
        else:
            cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls) -> None:
        """Create the playwright instance and start the browser."""
        super().tearDownClass()
        cls.browser.close()
        cls.playwright.stop()

    @pytest.fixture(scope="class", autouse=True)
    def playwright_user(self) -> User:
        """Create a test user to log in to the application with."""
        self.user = User.objects.create_user(username="playwright-user", password="xF7tgvnRmxux")
        return self.user

    def login(self, page: Page) -> None:
        """Log in to the application."""
        page.goto(self.live_server_url + reverse("login"))

        # Log in using Playwright syntax - use cls.username and cls.password
        page.fill('input[name="username"]', "playwright-user")
        page.fill('input[name="password"]', "xF7tgvnRmxux")
        page.press('input[name="password"]', "Enter")

        # Wait for the login to complete and redirect to the home page
        page.wait_for_selector("#logout-btn", timeout=10000)

    def test_profile_title(self) -> None:
        """Test that the title of the profile page is set correctly."""
        page = self.browser.new_page()
        self.login(page)
        page.goto(self.live_server_url + reverse("recordtransfer:user_profile"))
        expect(page).to_have_title("Your Profile")
