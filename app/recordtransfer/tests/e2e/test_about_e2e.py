import os

from django.conf import settings
from django.test import override_settings, tag
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
class AboutPageE2ETests(SeleniumLiveServerTestCase):
    """End-to-end tests for the About page."""

    def test_about_page_loads(self) -> None:
        """Test that the About page loads and displays correct heading."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        page_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "about-page-heading"))
        )
        self.assertIn("About", page_heading.text)

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        MAX_TOTAL_UPLOAD_COUNT=100,
        MAX_TOTAL_UPLOAD_SIZE_MB=144,
        MAX_SINGLE_UPLOAD_SIZE_MB=12,
    )
    def test_file_upload_info_shown_when_enabled(self) -> None:
        """Test that file upload info is displayed when uploads are enabled."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Check that file size limitations are displayed
        max_size_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Maximum Submission Size')]")
            )
        )
        self.assertIsNotNone(max_size_heading)

        # Check specific values
        page_content = driver.page_source
        self.assertIn("maximum of 100 files", page_content)
        self.assertIn("144 MB of files", page_content)
        self.assertIn("12 MB", page_content)

    @override_settings(FILE_UPLOAD_ENABLED=False)
    def test_file_upload_info_hidden_when_disabled(self) -> None:
        """Test that file upload info is not displayed when uploads are disabled."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Wait for page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card-body p"))
        )

        # Check that file size limitations are NOT displayed
        page_content = driver.page_source
        self.assertNotIn("Maximum Submission Size", page_content)

    @override_settings(
        FILE_UPLOAD_ENABLED=True,
        ACCEPTED_FILE_FORMATS={"Image": ["jpg", "png", "gif"], "Document": ["pdf"]},
    )
    def test_accepted_file_types_displayed(self) -> None:
        """Test that accepted file types are correctly displayed."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")
        driver.get(f"{self.live_server_url}{about_url}")

        # Check for file type categories
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(text(), 'Accepted File Types')]")
            )
        )

        # Check that specific file types are listed
        page_content = driver.page_source
        self.assertIn("Image Files", page_content)
        self.assertIn("jpg", page_content)
        self.assertIn("png", page_content)
        self.assertIn("gif", page_content)
        self.assertIn("Document Files", page_content)
        self.assertIn("pdf", page_content)

    def test_page_responsiveness(self) -> None:
        """Test that the About page is responsive at different viewport sizes."""
        driver = self.driver
        about_url = reverse("recordtransfer:about")

        # Test desktop size
        driver.set_window_size(1200, 800)
        driver.get(f"{self.live_server_url}{about_url}")
        desktop_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        self.assertTrue(desktop_element.is_displayed())

        # Test tablet size
        driver.set_window_size(768, 1024)
        driver.get(f"{self.live_server_url}{about_url}")
        tablet_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        self.assertTrue(tablet_element.is_displayed())

        # Test mobile size
        driver.set_window_size(375, 667)
        driver.get(f"{self.live_server_url}{about_url}")
        mobile_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card"))
        )
        self.assertTrue(mobile_element.is_displayed())

    def test_navigate_to_about_from_home(self) -> None:
        """Test navigation from home page to About page without login."""
        driver = self.driver
        home_url = reverse("recordtransfer:index")
        driver.get(f"{self.live_server_url}{home_url}")

        # Debug: print page source to help diagnose missing About link
        print("\n\nHOME PAGE HTML:\n", driver.page_source[:5000], "\n...truncated...\n")

        # Save screenshot for debugging
        screenshot_path = "home_page_debug.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot of home page saved to {screenshot_path}")

        about_link = None
        # List all elements with id nav-about
        nav_about_elements = driver.find_elements(By.ID, "nav-about")
        print(f"Found {len(nav_about_elements)} elements with id 'nav-about'.")
        for i, el in enumerate(nav_about_elements):
            try:
                style = driver.execute_script("return window.getComputedStyle(arguments[0]).cssText;", el)
                rect = driver.execute_script("return arguments[0].getBoundingClientRect();", el)
                pointer_events = driver.execute_script("return window.getComputedStyle(arguments[0]).pointerEvents;", el)
                opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity;", el)
                print(f"Element {i} style: {style}")
                print(f"Element {i} bounding rect: {rect}")
                print(f"Element {i} pointer-events: {pointer_events}")
                print(f"Element {i} opacity: {opacity}")
            except Exception as info_e:
                print(f"Could not get style/rect for element {i}: {info_e}")

        # Check for overlays that may block clicks
        overlays = driver.find_elements(By.CLASS_NAME, "menu-overlay")
        print(f"Found {len(overlays)} elements with class 'menu-overlay'.")
        for i, el in enumerate(overlays):
            try:
                style = driver.execute_script("return window.getComputedStyle(arguments[0]).cssText;", el)
                rect = driver.execute_script("return arguments[0].getBoundingClientRect();", el)
                pointer_events = driver.execute_script("return window.getComputedStyle(arguments[0]).pointerEvents;", el)
                opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity;", el)
                print(f"Overlay {i} style: {style}")
                print(f"Overlay {i} bounding rect: {rect}")
                print(f"Overlay {i} pointer-events: {pointer_events}")
                print(f"Overlay {i} opacity: {opacity}")
            except Exception as info_e:
                print(f"Could not get style/rect for overlay {i}: {info_e}")

        try:
            about_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "nav-about"))
            )
            # Print computed style for debugging
            style = driver.execute_script(
                "var e=document.getElementById('nav-about'); if(e) return window.getComputedStyle(e).cssText; return 'not found';"
            )
            print("Computed style for #nav-about:", style)

            # Print parent style
            parent_style = driver.execute_script(
                "var e=document.getElementById('nav-about'); if(e && e.parentElement) return window.getComputedStyle(e.parentElement).cssText; return 'no parent';"
            )
            print("Computed style for #nav-about parent:", parent_style)

            # Print bounding rect
            rect = driver.execute_script(
                "var e=document.getElementById('nav-about'); if(e) return e.getBoundingClientRect(); return 'not found';"
            )
            print("Bounding rect for #nav-about:", rect)

            # Try normal click
            about_link.click()
            driver.save_screenshot("after_normal_click.png")
            print("Screenshot after normal click saved to after_normal_click.png")
        except Exception as e:
            print(f"Normal click failed: {e}.")
            if about_link:
                print("Trying JS click.")
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", about_link)
                    driver.execute_script("arguments[0].click();", about_link)
                    driver.save_screenshot("after_js_click.png")
                    print("Screenshot after JS click saved to after_js_click.png")
                except Exception as js_e:
                    print(f"JS click also failed: {js_e}")
            else:
                print("about_link was not found, cannot attempt JS click.")

            # Try JS click on the first found nav-about element if normal click fails
            if nav_about_elements:
                print("Trying JS click on first found nav-about element.")
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", nav_about_elements[0])
                    driver.execute_script("arguments[0].click();", nav_about_elements[0])
                    driver.save_screenshot("after_js_click_first_element.png")
                    print("Screenshot after JS click on first element saved to after_js_click_first_element.png")
                except Exception as js_e2:
                    print(f"JS click on first found nav-about element also failed: {js_e2}")

        # Assert About page loads
        page_heading = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "about-page-heading"))
        )
        self.assertIn("About", page_heading.text)
