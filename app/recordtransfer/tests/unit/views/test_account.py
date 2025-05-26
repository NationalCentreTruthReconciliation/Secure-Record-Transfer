"""Tests for account creation and activation views."""

import logging
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from recordtransfer.forms import SignUpForm

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
        self.assertTemplateUsed(response, "recordtransfer/signupform.html")

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
