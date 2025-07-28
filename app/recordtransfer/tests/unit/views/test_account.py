"""Tests for account creation and activation views."""

import datetime
import logging
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from freezegun import freeze_time

from recordtransfer.forms import SignUpForm
from recordtransfer.tokens import account_activation_token

User = get_user_model()


class TestCreateAccount(TestCase):
    """Tests for the CreateAccount view."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def setUp(self) -> None:
        """Set up test data."""
        # Patch the ReCaptchaField clean method to avoid requiring actual captcha validation
        self.mock_clean_patcher = patch("django_recaptcha.fields.ReCaptchaField.clean")
        self.mock_clean = self.mock_clean_patcher.start()
        self.mock_clean.return_value = "PASSED"

        # Mock the send_user_activation_email task
        self.mock_email_patcher = patch("recordtransfer.emails.send_user_activation_email.delay")
        self.mock_send_email = self.mock_email_patcher.start()

        self.addCleanup(self.mock_clean_patcher.stop)
        self.addCleanup(self.mock_email_patcher.stop)

        self.create_account_url = reverse("recordtransfer:create_account")
        self.valid_form_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password1": "securepassword123",
            "password2": "securepassword123",
        }

        # Create an existing user for testing duplicate scenarios
        self.existing_user = User.objects.create_user(
            username="existinguser",
            first_name="Existing",
            last_name="User",
            email="existing@example.com",
            password="password123",
        )

    def test_get_create_account_unauthenticated(self) -> None:
        """Test GET request to create account page for unauthenticated user."""
        response = self.client.get(self.create_account_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create a New Account")
        self.assertIsInstance(response.context["form"], SignUpForm)
        self.assertTemplateUsed(response, "recordtransfer/signup.html")

    def test_get_create_account_authenticated_user_redirected(self) -> None:
        """Test that authenticated users are redirected to homepage."""
        self.client.force_login(self.existing_user)
        response = self.client.get(self.create_account_url)
        self.assertRedirects(response, reverse("recordtransfer:index"))

    def test_post_create_account_authenticated_user_redirected(self) -> None:
        """Test that authenticated users are redirected from POST requests too."""
        self.client.force_login(self.existing_user)
        response = self.client.post(self.create_account_url, data=self.valid_form_data)
        self.assertRedirects(response, reverse("recordtransfer:index"))

    def test_post_valid_form_creates_user_and_sends_email(self) -> None:
        """Test successful account creation with valid form data."""
        initial_user_count = User.objects.count()

        response = self.client.post(self.create_account_url, data=self.valid_form_data)

        # Check redirect to activation sent page
        self.assertRedirects(response, reverse("recordtransfer:activation_sent"))

        # Check user was created
        self.assertEqual(User.objects.count(), initial_user_count + 1)

        # Check user properties
        new_user = User.objects.get(username="testuser123")
        self.assertEqual(new_user.first_name, "Test")
        self.assertEqual(new_user.last_name, "User")
        self.assertEqual(new_user.email, "testuser@example.com")
        self.assertFalse(new_user.is_active)  # User should be inactive initially
        self.assertFalse(new_user.gets_submission_email_updates)
        self.assertTrue(new_user.check_password("securepassword123"))

        # Check activation email was sent
        self.mock_send_email.assert_called_once_with(new_user)

    def test_post_invalid_form_displays_errors(self) -> None:
        """Test form submission with invalid data shows errors."""
        invalid_data = self.valid_form_data.copy()
        invalid_data["password2"] = "different_password"

        response = self.client.post(self.create_account_url, data=invalid_data)

        # Should stay on the same page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create a New Account")

        # Check that form has errors on password2 field
        self.assertTrue(response.context["form"].errors.get("password2"))

        # User should not be created
        self.assertFalse(User.objects.filter(username="testuser123").exists())

        # Email should not be sent
        self.mock_send_email.assert_not_called()

    def test_post_duplicate_username_error(self) -> None:
        """Test that duplicate username shows error."""
        form_data = self.valid_form_data.copy()
        form_data["username"] = "existinguser"

        response = self.client.post(self.create_account_url, data=form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("username"))
        self.mock_send_email.assert_not_called()

    def test_post_duplicate_email_error(self) -> None:
        """Test that duplicate email shows error."""
        form_data = self.valid_form_data.copy()
        form_data["email"] = "existing@example.com"

        response = self.client.post(self.create_account_url, data=form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("email"))
        self.mock_send_email.assert_not_called()

    def test_post_missing_required_fields(self) -> None:
        """Test form validation for missing required fields."""
        # Test missing email
        form_data = self.valid_form_data.copy()
        del form_data["email"]

        response = self.client.post(self.create_account_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("email"))
        self.mock_send_email.assert_not_called()

    def test_post_short_username(self) -> None:
        """Test that username shorter than 6 characters is rejected."""
        form_data = self.valid_form_data.copy()
        form_data["username"] = "short"

        response = self.client.post(self.create_account_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("username"))
        self.mock_send_email.assert_not_called()

    def test_post_short_name_fields(self) -> None:
        """Test that names shorter than 2 characters are rejected."""
        # Test short first name
        form_data = self.valid_form_data.copy()
        form_data["first_name"] = "T"

        response = self.client.post(self.create_account_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("first_name"))
        # Test short last name
        form_data = self.valid_form_data.copy()
        form_data["last_name"] = "U"

        response = self.client.post(self.create_account_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("last_name"))
        self.mock_send_email.assert_not_called()

    def test_post_invalid_email_format(self) -> None:
        """Test that invalid email format is rejected."""
        form_data = self.valid_form_data.copy()
        form_data["email"] = "invalid-email-format"

        response = self.client.post(self.create_account_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("email"))
        self.mock_send_email.assert_not_called()

    def test_post_case_insensitive_email_duplicate(self) -> None:
        """Test that email duplicate check is case insensitive."""
        form_data = self.valid_form_data.copy()
        form_data["email"] = "EXISTING@EXAMPLE.COM"

        response = self.client.post(self.create_account_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors.get("email"))
        self.mock_send_email.assert_not_called()

    def test_email_mock_behavior(self) -> None:
        """Test that email sending mock is working correctly."""
        # Submit valid form
        self.client.post(self.create_account_url, data=self.valid_form_data)

        # Verify mock was called correctly
        self.assertTrue(self.mock_send_email.called)
        self.assertEqual(self.mock_send_email.call_count, 1)

        # Get the user that was passed to the email function
        called_user = self.mock_send_email.call_args[0][0]
        self.assertEqual(called_user.username, "testuser123")
        self.assertEqual(called_user.email, "testuser@example.com")

    def test_user_defaults_set_correctly(self) -> None:
        """Test that user defaults are set correctly during creation."""
        self.client.post(self.create_account_url, data=self.valid_form_data)

        new_user = User.objects.get(username="testuser123")

        # These should be set to False by the view
        self.assertFalse(new_user.is_active)
        self.assertFalse(new_user.gets_submission_email_updates)

        # These should be default Django user fields
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)

    def test_htmx_post_valid_form(self) -> None:
        """Test successful account creation via HTMX request."""
        initial_user_count = User.objects.count()

        response = self.client.post(
            self.create_account_url,
            data=self.valid_form_data,
            HTTP_HX_REQUEST="true",
        )

        # Check for HX-Redirect response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["HX-Redirect"], reverse("recordtransfer:activation_sent")
        )

        # Check user was created
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        new_user = User.objects.get(username="testuser123")
        self.assertFalse(new_user.is_active)

        # Check activation email was sent
        self.mock_send_email.assert_called_once_with(new_user)

    def test_htmx_post_invalid_form(self) -> None:
        """Test form submission with invalid data via HTMX request."""
        invalid_data = self.valid_form_data.copy()
        invalid_data["password2"] = "different_password"

        response = self.client.post(
            self.create_account_url,
            data=invalid_data,
            HTTP_HX_REQUEST="true",
        )

        # Check for HX-Redirect response
        self.assertEqual(response.status_code, 200)
        self.assertIn("Create a New Account", str(response.content))

        # Test that form is invalid

        form = SignUpForm(data=invalid_data)
        self.assertFalse(form.is_valid())

        # User should not be created
        self.assertFalse(User.objects.filter(username="testuser123").exists())

        # Email should not be sent
        self.mock_send_email.assert_not_called()

    def test_htmx_post_empty_form(self) -> None:
        """Test HTMX submission with empty form data."""
        user_count_before_request = User.objects.count()
        response = self.client.post(
            self.create_account_url,
            data={},  # Empty data
            HTTP_HX_REQUEST="true",
        )

        # Should return form with errors
        self.assertEqual(response.status_code, 200)

        # Should contain error indicators
        self.assertIn("alert-error", str(response.content))

        required_fields = {
            "username": "This field is required",
            "first_name": "This field is required",
            "last_name": "This field is required",
            "email": "This field is required",
            "password1": "This field is required",
            "password2": "This field is required",
        }

        for field, error_message in required_fields.items():
            # Verify field exists in the response
            self.assertIn(f"id_{field}", str(response.content))
            # Verify the specific error message appears for this field
            self.assertIn(error_message, str(response.content))

        # User should not be created
        self.assertEqual(User.objects.count(), user_count_before_request)


class TestActivateAccount(TestCase):
    """Tests for the ActivateAccount view."""

    def setUp(self) -> None:
        """Set up test data."""
        # Create inactive user for activation tests
        self.inactive_user = User.objects.create_user(
            username="inactiveuser",
            first_name="Inactive",
            last_name="User",
            email="inactive@example.com",
            password="password123",
            is_active=False,
        )

        # Create active user for testing already activated scenarios
        self.active_user = User.objects.create_user(
            username="activeuser",
            first_name="Active",
            last_name="User",
            email="active@example.com",
            password="password123",
            is_active=True,
        )

        # Generate valid activation token and uidb64
        self.valid_token = account_activation_token.make_token(self.inactive_user)
        self.valid_uidb64 = urlsafe_base64_encode(force_bytes(self.inactive_user.pk))

        # Generate invalid token and uidb64
        self.invalid_token = "invalid-token-123"
        self.invalid_uidb64 = urlsafe_base64_encode(force_bytes(99999))  # Non-existent user ID

    def test_activate_account_valid_token(self) -> None:
        """Test successful account activation with valid token."""
        activate_url = reverse(
            "recordtransfer:activate_account",
            kwargs={"uidb64": self.valid_uidb64, "token": self.valid_token},
        )

        response = self.client.get(activate_url)

        # Should redirect to success page
        self.assertRedirects(response, reverse("recordtransfer:account_created"))

        # User should now be active and logged in
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_activate_account_invalid_token(self) -> None:
        """Test activation with invalid token shows error."""
        activate_url = reverse(
            "recordtransfer:activate_account",
            kwargs={"uidb64": self.valid_uidb64, "token": self.invalid_token},
        )

        response = self.client.get(activate_url)

        # Should redirect to invalid activation page
        self.assertRedirects(response, reverse("recordtransfer:activation_invalid"))

        # User should remain inactive and not logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)

    def test_activate_account_invalid_uidb64(self) -> None:
        """Test activation with invalid user ID shows error."""
        activate_url = reverse(
            "recordtransfer:activate_account",
            kwargs={"uidb64": self.invalid_uidb64, "token": self.valid_token},
        )

        response = self.client.get(activate_url)

        # Should redirect to invalid activation page
        self.assertRedirects(response, reverse("recordtransfer:activation_invalid"))

        # User should remain inactive and not logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)

    def test_activate_account_already_active_user(self) -> None:
        """Test activation of already active user."""
        # Generate token for active user
        token = account_activation_token.make_token(self.active_user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.active_user.pk))

        activate_url = reverse(
            "recordtransfer:activate_account", kwargs={"uidb64": uidb64, "token": token}
        )

        response = self.client.get(activate_url)

        # Should redirect to invalid activation page
        self.assertRedirects(response, reverse("recordtransfer:activation_invalid"))

        # User should remain active and not logged in
        self.active_user.refresh_from_db()
        self.assertTrue(self.active_user.is_active)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_activate_account_on_user_activated_after_token_creation(self) -> None:
        """Test that actiavation fails if user was activated after token creation."""
        self.inactive_user.is_active = True
        self.inactive_user.save()

        activate_url = reverse(
            "recordtransfer:activate_account",
            kwargs={"uidb64": self.valid_uidb64, "token": self.valid_token},
        )
        response = self.client.get(activate_url)

        # Should redirect to invalid activation page
        self.assertRedirects(response, reverse("recordtransfer:activation_invalid"))

        # User should remain active and not logged in
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)

    def test_activate_account_authenticated_user_redirected(self) -> None:
        """Test that authenticated users are redirected to homepage."""
        self.client.force_login(self.active_user)

        activate_url = reverse(
            "recordtransfer:activate_account",
            kwargs={"uidb64": self.valid_uidb64, "token": self.valid_token},
        )

        response = self.client.get(activate_url)
        self.assertRedirects(response, reverse("recordtransfer:index"))

    def test_activate_account_malformed_uidb64(self) -> None:
        """Test activation with malformed uidb64 shows error."""
        activate_url = reverse(
            "recordtransfer:activate_account",
            kwargs={"uidb64": "malformed-uid", "token": self.valid_token},
        )

        response = self.client.get(activate_url)

        # Should redirect to invalid activation page
        self.assertRedirects(response, reverse("recordtransfer:activation_invalid"))

        # User should remain inactive and not logged in
        self.inactive_user.refresh_from_db()
        self.assertFalse(self.inactive_user.is_active)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


@override_settings(AXES_ENABLED=True)
class TestLogin(TestCase):
    """Tests for the Login view."""

    def setUp(self) -> None:
        """Set up test data."""
        self.login_url = reverse("login")

        # Create a test user
        self.test_user = User.objects.create_user(
            username="testloginuser",
            first_name="Test",
            last_name="Login",
            email="login@example.com",
            password="securepassword123",
            is_active=True,
        )

        # Create an inactive test user
        self.inactive_user = User.objects.create_user(
            username="inactiveloginuser",
            first_name="Inactive",
            last_name="User",
            email="inactive@example.com",
            password="securepassword123",
            is_active=False,
        )

        self.valid_credentials = {
            "username": "testloginuser",
            "password": "securepassword123",
        }

        self.invalid_credentials = {
            "username": "testloginuser",
            "password": "wrongpassword",
        }

        self.inactive_credentials = {
            "username": "inactiveloginuser",
            "password": "securepassword123",
        }

    def test_get_login_page(self) -> None:
        """Test GET request to login page."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], self.login_url)
        self.assertIsInstance(response.context["form"], AuthenticationForm)

    def test_login_successful(self) -> None:
        """Test successful login with valid credentials."""
        response = self.client.post(self.login_url, self.valid_credentials)

        # Check redirect to default success URL
        self.assertRedirects(response, reverse("recordtransfer:index"))

        # Check user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "testloginuser")

    def test_login_invalid_credentials(self) -> None:
        """Test login with invalid credentials."""
        response = self.client.post(self.login_url, self.invalid_credentials)

        self.assertEqual(response.status_code, 200)
        # Check that we're still at the login URL (not redirected)
        self.assertEqual(response.request["PATH_INFO"], self.login_url)

        # Should have form errors
        self.assertTrue(response.context["form"].errors)

        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_inactive_user(self) -> None:
        """Test login with inactive user."""
        response = self.client.post(self.login_url, self.inactive_credentials)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], self.login_url)

        # Should have form errors
        self.assertTrue(response.context["form"].errors)

        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_htmx_login_successful(self) -> None:
        """Test HTMX login with valid credentials."""
        response = self.client.post(self.login_url, self.valid_credentials, HTTP_HX_REQUEST="true")

        # Should be a direct response with HX-Redirect header
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Redirect"], reverse("recordtransfer:index"))

        # Check user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "testloginuser")

    def test_htmx_login_invalid(self) -> None:
        """Test HTMX login with invalid credentials."""
        response = self.client.post(
            self.login_url, self.invalid_credentials, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)

        # Should contain error message
        self.assertIn("alert-error", str(response.content))

        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_htmx_login_inactive_user(self) -> None:
        """Test HTMX login with inactive user."""
        response = self.client.post(
            self.login_url, self.inactive_credentials, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)

        # Should contain error message
        self.assertIn("alert-error", str(response.content))

        # User should not be authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_redirect_to_next_parameter(self) -> None:
        """Test that login redirects to next parameter if provided."""
        next_url = reverse("recordtransfer:user_profile")
        response = self.client.post(self.login_url + f"?next={next_url}", self.valid_credentials)

        # Should redirect to the next URL
        self.assertRedirects(response, next_url)

        # User should be authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "testloginuser")
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        # Logout
        self.client.logout()
        # Failed attempts should reset, so lockout should not trigger after 1 more fail
        response = self.client.post(self.login_url, self.invalid_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    @override_settings(AXES_FAILURE_LIMIT=3, AXES_COOLOFF_TIME=0.01)
    def test_lockout_after_failed_attempts(self) -> None:
        """User is locked out after too many failed login attempts."""
        for _ in range(2):
            response = self.client.post(self.login_url, self.invalid_credentials)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.wsgi_request.user.is_authenticated)
        # 3rd attempt should trigger lockout
        response = self.client.post(self.login_url, self.invalid_credentials)
        self.assertEqual(response.status_code, 429)

    @override_settings(AXES_FAILURE_LIMIT=2, AXES_COOLOFF_TIME=1)
    def test_login_after_lockout_period(self) -> None:
        """User can log in after lockout period expires."""
        login_url = reverse("login")
        for _ in range(2):
            self.client.post(login_url, self.invalid_credentials)
        # Locked out
        response = self.client.post(login_url, self.valid_credentials)
        self.assertEqual(response.status_code, 429)

        # Calculate unlock time based on AXES_COOLOFF_TIME
        unlock_time = timezone.now() + datetime.timedelta(hours=settings.AXES_COOLOFF_TIME)

        with freeze_time(unlock_time):
            response = self.client.post(login_url, self.valid_credentials)
            self.assertEqual(response.status_code, 302)  # Is this the expected behaviour?
            self.assertRedirects(response, reverse("recordtransfer:index"))
            self.assertTrue(response.wsgi_request.user.is_authenticated)

    @override_settings(AXES_FAILURE_LIMIT=2, AXES_COOLOFF_TIME=0.01)
    def test_lockout_resets_after_successful_login(self) -> None:
        """Lockout counter resets after successful login."""
        # 1 failed attempt
        self.client.post(self.login_url, self.invalid_credentials)
        # Successful login
        response = self.client.post(self.login_url, self.valid_credentials)
        self.assertRedirects(response, reverse("recordtransfer:index"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.client.logout()
        # Log back in
        response = self.client.post(self.login_url, self.valid_credentials)
        self.assertRedirects(response, reverse("recordtransfer:index"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    # @override_settings(AXES_FAILURE_LIMIT=2, AXES_COOLOFF_TIME=0.001)
    # def test_failed_attempt_during_lockout_resets_timer(self) -> None:
    #     """A failed login during lockout resets the lockout timer."""
    #     login_url = reverse("login")
    #     for _ in range(2):
    #         self.client.post(login_url, self.invalid_credentials)
    #     # Locked out
    #     response = self.client.post(login_url, self.valid_credentials)
    #     self.assertEqual(response.status_code, 429)
    #     # Advance time just before unlock
    #     cooloff_minutes = int(settings.AXES_COOLOFF_TIME * 60)
    #     almost_unlock = datetime.datetime.now() + datetime.timedelta(minutes=cooloff_minutes - 1)
    #     with freeze_time(almost_unlock):
    #         # Another failed attempt should reset timer
    #         response = self.client.post(login_url, self.invalid_credentials)
    #         self.assertEqual(response.status_code, 429)
    #         # Now advance time again, should still be locked out
    #         unlock_time = datetime.datetime.now() + datetime.timedelta(minutes=cooloff_minutes)
    #         with freeze_time(unlock_time):
    #             response = self.client.post(login_url, self.valid_credentials)
    #             self.assertEqual(response.status_code, 429)
