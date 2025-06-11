from enum import Enum
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from recordtransfer.forms.admin_forms import SiteSettingModelForm
from recordtransfer.models import SiteSetting, User


class TestSiteSettingModelForm(TestCase):
    """Tests for the SiteSettingModelForm."""

    # Create TestKey by combining necessary key-value pairs from SiteSetting.Key enum with custom
    # key-value pairs for testing
    class TestKey(Enum):
        """Test-specific keys for SiteSetting."""

        # Copy necessary keys from SiteSetting.Key
        PAGINATE_BY = SiteSetting.Key.PAGINATE_BY.value
        ARCHIVIST_EMAIL = SiteSetting.Key.ARCHIVIST_EMAIL.value

        # Add test-specific keys
        TEST_STRING_SETTING = "TEST_STRING_SETTING"
        TEST_INT_SETTING = "TEST_INT_SETTING"

        @property
        def description(self) -> str:
            """Return a description for the test key."""
            return "Test description"

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(username="testuser", password="password")

        # Create test settings
        self.string_setting = SiteSetting.objects.create(
            key="TEST_STRING_SETTING",
            value="test value",
            value_type=SiteSetting.SettingType.STR,
            changed_by=self.user,
        )

        self.int_setting = SiteSetting.objects.create(
            key="TEST_INT_SETTING",
            value="42",
            value_type=SiteSetting.SettingType.INT,
            changed_by=self.user,
        )

        self.paginate_setting = SiteSetting.objects.get(
            key=SiteSetting.Key.PAGINATE_BY.value,
        )

        self.email_setting = SiteSetting.objects.get(
            key=SiteSetting.Key.ARCHIVIST_EMAIL.value,
        )

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_string_valid(self) -> None:
        """Test clean_value with valid string value."""
        form = SiteSettingModelForm(
            data={"value": "new string value"}, instance=self.string_setting
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["value"], "new string value")

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_string_empty(self) -> None:
        """Test clean_value with empty string value."""
        form = SiteSettingModelForm(data={"value": "   "}, instance=self.string_setting)
        self.assertFalse(form.is_valid())

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_string_none(self) -> None:
        """Test clean_value with None value for string setting."""
        form = SiteSettingModelForm(data={}, instance=self.string_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["value"])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_int_valid(self) -> None:
        """Test clean_value with valid integer string."""
        form = SiteSettingModelForm(data={"value": "123"}, instance=self.int_setting)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["value"], "123")

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_int_negative(self) -> None:
        """Test clean_value with negative integer string."""
        form = SiteSettingModelForm(data={"value": "-10"}, instance=self.int_setting)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["value"], "-10")

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_int_invalid(self) -> None:
        """Test clean_value with invalid integer string."""
        form = SiteSettingModelForm(data={"value": "not a number"}, instance=self.int_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("Value must be a valid whole number.", form.errors["value"][0])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_value_int_float(self) -> None:
        """Test clean_value with float string for integer setting."""
        form = SiteSettingModelForm(data={"value": "12.5"}, instance=self.int_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("Value must be a valid whole number.", form.errors["value"][0])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_paginate_by_valid(self) -> None:
        """Test clean method with valid PAGINATE_BY value."""
        form = SiteSettingModelForm(data={"value": "50"}, instance=self.paginate_setting)
        self.assertTrue(form.is_valid())

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_paginate_by_zero(self) -> None:
        """Test clean method with zero PAGINATE_BY value."""
        form = SiteSettingModelForm(data={"value": "0"}, instance=self.paginate_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("PAGINATE_BY must be a positive whole number.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_paginate_by_negative(self) -> None:
        """Test clean method with negative PAGINATE_BY value."""
        form = SiteSettingModelForm(data={"value": "-5"}, instance=self.paginate_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("PAGINATE_BY must be a positive whole number.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_paginate_by_invalid_string(self) -> None:
        """Test clean method with invalid string for PAGINATE_BY."""
        form = SiteSettingModelForm(data={"value": "invalid"}, instance=self.paginate_setting)
        self.assertFalse(form.is_valid())
        # Should fail at clean_value level first
        self.assertIn("Value must be a valid whole number.", form.errors["value"][0])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_archivist_email_valid(self) -> None:
        """Test clean method with valid email address."""
        form = SiteSettingModelForm(data={"value": "new@example.com"}, instance=self.email_setting)
        self.assertTrue(form.is_valid())

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_archivist_email_invalid(self) -> None:
        """Test clean method with invalid email address."""
        form = SiteSettingModelForm(data={"value": "invalid-email"}, instance=self.email_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("ARCHIVIST_EMAIL must be a valid email address.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_archivist_email_empty(self) -> None:
        """Test clean method with empty email address."""
        form = SiteSettingModelForm(data={"value": ""}, instance=self.email_setting)
        self.assertFalse(form.is_valid())
        # Should fail at clean level for empty value
        self.assertIn("ARCHIVIST_EMAIL cannot be empty.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSetting.Key", TestKey)
    def test_clean_empty_value_generic(self) -> None:
        """Test clean method with empty value for generic setting."""
        form = SiteSettingModelForm(data={"value": ""}, instance=self.string_setting)
        self.assertFalse(form.is_valid())
        # Should fail at both clean_value and clean levels
        self.assertTrue(
            "Value must be a non-empty text value." in form.errors.get("value", [])
            or "TEST_STRING_SETTING cannot be empty." in form.errors.get("__all__", [])
        )

    @patch("recordtransfer.forms.admin_forms.validate_email")
    def test_clean_email_validation_error_handling(self, mock_validate_email: MagicMock) -> None:
        """Test that email validation errors are properly handled."""
        mock_validate_email.side_effect = ValidationError("Invalid email")

        form = SiteSettingModelForm(data={"value": "bad@email"}, instance=self.email_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("ARCHIVIST_EMAIL must be a valid email address.", form.errors["__all__"])
