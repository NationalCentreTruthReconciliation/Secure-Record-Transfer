from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from recordtransfer.validators import (
    CharacterCategoriesValidator,
    ContainsUserNameValidator,
    LengthRangeValidator,
    PasswordHistoryValidator,
)


class LengthRangeValidatorTestCase(TestCase):
    """Tests for the password length range validator."""

    def test_password_too_short(self) -> None:
        """Test when the password is too short."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        with self.assertRaises(ValidationError) as cm:
            target.validate("123456789")

        self.assertEqual(cm.exception.code, "password_too_short")
        self.assertIn("at least 10 characters", str(cm.exception))

    def test_password_too_long(self) -> None:
        """Test when the password is too long."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        with self.assertRaises(ValidationError) as cm:
            target.validate("A" * 31)

        self.assertEqual(cm.exception.code, "password_too_long")
        self.assertIn("at most 30 characters", str(cm.exception))

    def test_password_exactly_min_length(self) -> None:
        """Test when password is exactly at minimum length."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        # Should not raise an exception
        target.validate("A" * 10)

    def test_password_exactly_max_length(self) -> None:
        """Test when password is exactly at maximum length."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        # Should not raise an exception
        target.validate("A" * 30)

    def test_password_within_range(self) -> None:
        """Test when password is within the valid range."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        # Should not raise an exception
        target.validate("ValidPassword123!")

    def test_empty_password(self) -> None:
        """Test with empty password."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        with self.assertRaises(ValidationError) as cm:
            target.validate("")

        self.assertEqual(cm.exception.code, "password_too_short")

    def test_none_password(self) -> None:
        """Test with None password."""
        target = LengthRangeValidator(min_length=10, max_length=30)

        with self.assertRaises(ValidationError) as cm:
            target.validate(None)

        self.assertEqual(cm.exception.code, "password_too_short")

    def test_custom_lengths(self) -> None:
        """Test with custom min/max lengths."""
        target = LengthRangeValidator(min_length=5, max_length=15)

        # Test boundaries
        target.validate("A" * 5)  # Min
        target.validate("A" * 15)  # Max

        with self.assertRaises(ValidationError):
            target.validate("A" * 4)  # Below min

        with self.assertRaises(ValidationError):
            target.validate("A" * 16)  # Above max


class CharacterCategoriesValidatorTestCase(TestCase):
    """Tests for the character categories validator."""

    def test_password_with_all_categories(self) -> None:
        """Test password containing all four character categories."""
        target = CharacterCategoriesValidator()

        # Should not raise an exception
        target.validate("Abc123!@#")

    def test_password_with_three_categories(self) -> None:
        """Test password containing exactly three categories (minimum required)."""
        target = CharacterCategoriesValidator()

        # Should not raise an exception
        target.validate("Abc123")  # Upper, lower, digits
        target.validate("Abc!@#")  # Upper, lower, special
        target.validate("ABC123!")  # Upper, digits, special
        target.validate("abc123!")  # Lower, digits, special

    def test_password_with_two_categories(self) -> None:
        """Test password with only two categories (should fail)."""
        target = CharacterCategoriesValidator()

        with self.assertRaises(ValidationError) as cm:
            target.validate("Abcdef")  # Only upper and lower

        self.assertEqual(cm.exception.code, "password_not_enough_categories")
        self.assertIn("at least 3", str(cm.exception))

    def test_password_with_one_category(self) -> None:
        """Test password with only one category (should fail)."""
        target = CharacterCategoriesValidator()

        with self.assertRaises(ValidationError) as cm:
            target.validate("ABCDEF")  # Only upper case

        self.assertEqual(cm.exception.code, "password_not_enough_categories")

    def test_password_with_no_categories(self) -> None:
        """Test password with no valid categories (edge case)."""
        target = CharacterCategoriesValidator()

        with self.assertRaises(ValidationError):
            target.validate("")  # Empty string

    def test_custom_required_categories(self) -> None:
        """Test with custom required category count."""
        target = CharacterCategoriesValidator(required_categories=2)

        # Should pass with 2 categories
        target.validate("Abcdef")  # Upper and lower

        # Should fail with 1 category
        with self.assertRaises(ValidationError):
            target.validate("ABCDEF")  # Only upper

    def test_custom_special_characters(self) -> None:
        """Test with custom allowed special characters."""
        target = CharacterCategoriesValidator(allowed_specials="!@#$%")

        # Should pass with custom specials
        target.validate("Abc123!@#")

        with self.assertRaises(ValidationError):
            target.validate("Abcdef()")  # Only upper, lower (2 categories, need 3)

    def test_edge_case_special_characters(self) -> None:
        """Test edge cases with special characters."""
        target = CharacterCategoriesValidator()

        # Test with spaces (not in allowed set) - need to ensure it only has 2 categories
        with self.assertRaises(ValidationError):
            target.validate("Abc def")  # Only upper, lower (2 categories, need 3)


class PasswordHistoryValidatorTestCase(TestCase):
    """Tests for the password history validator."""

    def setUp(self) -> None:
        """Set up test user."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="InitialPassword123!"
        )

    def test_current_password_reuse(self) -> None:
        """Test that current password cannot be reused."""
        target = PasswordHistoryValidator()

        with self.assertRaises(ValidationError) as cm:
            target.validate("InitialPassword123!", self.user)

        self.assertEqual(cm.exception.code, "password_same_as_current")

    def test_empty_password(self) -> None:
        """Test behavior with empty password."""
        target = PasswordHistoryValidator()

        # Should not raise an exception
        target.validate("", self.user)

    def test_none_password(self) -> None:
        """Test behavior with None password."""
        target = PasswordHistoryValidator()

        # Should not raise an exception
        target.validate(None, self.user)

    def test_custom_history_depth(self) -> None:
        """Test with custom history depth."""
        target = PasswordHistoryValidator(history_depth=3)

        # Should not raise an exception for new password
        target.validate("NewPassword123!", self.user)


class ContainsUserNameValidatorTestCase(TestCase):
    """Tests for the user attribute containment validator."""

    def setUp(self) -> None:
        """Set up test user."""
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

    def test_password_contains_username(self) -> None:
        """Test password containing the username."""
        target = ContainsUserNameValidator()

        with self.assertRaises(ValidationError) as cm:
            target.validate("testuser123!", self.user)

        self.assertEqual(cm.exception.code, "password_contains_user_attribute")

    def test_password_contains_first_name(self) -> None:
        """Test password containing the first name."""
        target = ContainsUserNameValidator()

        with self.assertRaises(ValidationError) as cm:
            target.validate("John123!", self.user)

        self.assertEqual(cm.exception.code, "password_contains_user_attribute")

    def test_password_contains_last_name(self) -> None:
        """Test password containing the last name."""
        target = ContainsUserNameValidator()

        with self.assertRaises(ValidationError) as cm:
            target.validate("Doe123!", self.user)

        self.assertEqual(cm.exception.code, "password_contains_user_attribute")

    def test_password_contains_multiple_attributes(self) -> None:
        """Test password containing multiple user attributes."""
        target = ContainsUserNameValidator()

        with self.assertRaises(ValidationError):
            target.validate("JohnDoe123!", self.user)

    def test_password_does_not_contain_attributes(self) -> None:
        """Test password that doesn't contain user attributes."""
        target = ContainsUserNameValidator()

        # Should not raise an exception
        target.validate("SecurePassword123!", self.user)

    def test_case_insensitive_matching(self) -> None:
        """Test that matching is case insensitive."""
        target = ContainsUserNameValidator()

        with self.assertRaises(ValidationError):
            target.validate("JOHN123!", self.user)  # Uppercase first name

        with self.assertRaises(ValidationError):
            target.validate("doe123!", self.user)  # Lowercase last name

    def test_partial_matches_ignored(self) -> None:
        """Test that partial matches are ignored."""
        target = ContainsUserNameValidator()

        # Should not raise an exception
        target.validate("Jo123!", self.user)  # Partial first name
        target.validate("Do123!", self.user)  # Partial last name
        target.validate("test123!", self.user)  # Partial username

    def test_email_ignored(self) -> None:
        """Test that email is not checked."""
        target = ContainsUserNameValidator()

        # Should not raise an exception
        target.validate("test@example.com123!", self.user)

    def test_empty_user_attributes(self) -> None:
        """Test with user having empty attributes."""
        self.user.first_name = ""
        self.user.last_name = ""
        # Don't set username to empty as it's required
        self.user.save()

        target = ContainsUserNameValidator()

        # Should not raise an exception
        target.validate("AnyPassword123!", self.user)

    def test_empty_password(self) -> None:
        """Test behavior with empty password."""
        target = ContainsUserNameValidator()

        # Should not raise an exception
        target.validate("", self.user)

    def test_none_password(self) -> None:
        """Test behavior with None password."""
        target = ContainsUserNameValidator()

        # Should not raise an exception
        target.validate(None, self.user)

    def test_custom_user_attributes(self) -> None:
        """Test with custom user attributes to check."""
        # Create a new validator instance with custom attributes
        target = ContainsUserNameValidator()
        # Override the class attribute for this test
        target.user_attributes = ("username",)

        # Should fail with username
        with self.assertRaises(ValidationError):
            target.validate("testuser123!", self.user)

        # Should pass with first name (not in custom attributes)
        target.validate("John123!", self.user)
