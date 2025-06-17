from enum import Enum
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from recordtransfer.enums import SettingKeyMeta, SiteSettingKey, SiteSettingType
from recordtransfer.forms.admin_forms import SiteSettingModelForm
from recordtransfer.models import SiteSetting, User


class TestSiteSettingModelForm(TestCase):
    """Tests for the SiteSettingModelForm."""

    # Define a test-specific SiteSettingKey enum with additional test settings
    TestSiteSettingKey = Enum(
        "TestSiteSettingKey",
        {
            **SiteSettingKey.__members__,
            "TEST_STRING_SETTING": SettingKeyMeta(
                SiteSettingType.STR,
                ("This is a test string setting."),
                default_value="test-string-value",
            ),
            "TEST_INT_SETTING": SettingKeyMeta(
                SiteSettingType.INT,
                ("This is a test integer setting."),
                default_value="42",
            ),
        },
    )

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.user = User.objects.create_user(username="testuser", password="password")

        # Create test settings
        self.test_string_setting = SiteSetting.objects.create(
            key="TEST_STRING_SETTING",
            value="test value",
            value_type=SiteSettingType.STR,
            changed_by=self.user,
        )

        self.test_int_setting = SiteSetting.objects.create(
            key="TEST_INT_SETTING",
            value="42",
            value_type=SiteSettingType.INT,
            changed_by=self.user,
        )

        self.paginate_setting = SiteSetting.objects.get(
            key=SiteSettingKey.PAGINATE_BY.key_name,
        )

        self.email_setting = SiteSetting.objects.get(
            key=SiteSettingKey.ARCHIVIST_EMAIL.key_name,
        )

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_string_valid(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with valid string value."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test string setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(
            data={"value": "new string value"}, instance=self.test_string_setting
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["value"], "new string value")
        self.assertEqual(form.fields["value"].help_text, "This is a test string setting.")

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_string_empty(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with empty string value."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test string setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={"value": "   "}, instance=self.test_string_setting)
        self.assertFalse(form.is_valid())

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_string_none(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with None value for string setting."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test string setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={}, instance=self.test_string_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["value"])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_int_valid(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with valid integer string."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test integer setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={"value": "123"}, instance=self.test_int_setting)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["value"], "123")

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_int_negative(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with negative integer string."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test integer setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={"value": "-10"}, instance=self.test_int_setting)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["value"], "-10")

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_int_invalid(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with invalid integer string."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test integer setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={"value": "not a number"}, instance=self.test_int_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("Value must be a valid whole number.", form.errors["value"][0])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_value_int_float(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean_value with float string for integer setting."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test integer setting."
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={"value": "12.5"}, instance=self.test_int_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("Value must be a valid whole number.", form.errors["value"][0])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_paginate_by_valid(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with valid PAGINATE_BY value."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Number of items to display per page."
        mock_enum_member.key_name = "PAGINATE_BY"

        # Make the mock return the same object for both calls
        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.PAGINATE_BY = mock_enum_member

        form = SiteSettingModelForm(data={"value": "50"}, instance=self.paginate_setting)
        self.assertTrue(form.is_valid())

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_paginate_by_zero(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with zero PAGINATE_BY value."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Number of items to display per page."
        mock_enum_member.key_name = "PAGINATE_BY"

        # Make the mock return the same object for both calls
        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.PAGINATE_BY = mock_enum_member

        form = SiteSettingModelForm(data={"value": "0"}, instance=self.paginate_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("PAGINATE_BY must be a positive whole number.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_paginate_by_negative(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with negative PAGINATE_BY value."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Number of items to display per page."
        mock_enum_member.key_name = "PAGINATE_BY"

        # Make the mock return the same object for both calls
        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.PAGINATE_BY = mock_enum_member

        form = SiteSettingModelForm(data={"value": "-5"}, instance=self.paginate_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("PAGINATE_BY must be a positive whole number.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_paginate_by_invalid_string(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with invalid string for PAGINATE_BY."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Number of items to display per page."
        mock_enum_member.key_name = "PAGINATE_BY"

        # Make the mock return the same object for both calls
        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.PAGINATE_BY = mock_enum_member

        form = SiteSettingModelForm(data={"value": "invalid"}, instance=self.paginate_setting)
        self.assertFalse(form.is_valid())
        # Should fail at clean_value level first
        self.assertIn("Value must be a valid whole number.", form.errors["value"][0])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_archivist_email_valid(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with valid email address."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Email address of the archivist."
        mock_enum_member.key_name = "ARCHIVIST_EMAIL"

        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.ARCHIVIST_EMAIL = mock_enum_member

        form = SiteSettingModelForm(data={"value": "new@example.com"}, instance=self.email_setting)
        self.assertTrue(form.is_valid())

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_archivist_email_invalid(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with invalid email address."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Email address of the archivist."
        mock_enum_member.key_name = "ARCHIVIST_EMAIL"

        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.ARCHIVIST_EMAIL = mock_enum_member

        form = SiteSettingModelForm(data={"value": "invalid-email"}, instance=self.email_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("ARCHIVIST_EMAIL must be a valid email address.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_archivist_email_empty(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with empty email address."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Email address of the archivist."
        mock_enum_member.key_name = "ARCHIVIST_EMAIL"

        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.ARCHIVIST_EMAIL = mock_enum_member

        form = SiteSettingModelForm(data={"value": ""}, instance=self.email_setting)
        self.assertFalse(form.is_valid())
        # Should fail at clean level for empty value
        self.assertIn("ARCHIVIST_EMAIL cannot be empty.", form.errors["__all__"])

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    def test_clean_empty_value_generic(self, mock_site_setting_key: MagicMock) -> None:
        """Test clean method with empty value for generic setting."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "This is a test string setting."
        mock_enum_member.key_name = "TEST_STRING_SETTING"
        mock_site_setting_key.__getitem__.return_value = mock_enum_member

        form = SiteSettingModelForm(data={"value": ""}, instance=self.test_string_setting)
        self.assertFalse(form.is_valid())
        # Should fail at both clean_value and clean levels
        self.assertTrue(
            "Value must be a non-empty text value." in form.errors.get("value", [])
            or "TEST_STRING_SETTING cannot be empty." in form.errors.get("__all__", [])
        )

    @patch("recordtransfer.forms.admin_forms.SiteSettingKey")
    @patch("recordtransfer.forms.admin_forms.validate_email")
    def test_clean_email_validation_error_handling(
        self, mock_validate_email: MagicMock, mock_site_setting_key: MagicMock
    ) -> None:
        """Test that email validation errors are properly handled."""
        mock_enum_member = MagicMock()
        mock_enum_member.description = "Email address of the archivist."
        mock_enum_member.key_name = "ARCHIVIST_EMAIL"

        mock_site_setting_key.__getitem__.return_value = mock_enum_member
        mock_site_setting_key.return_value = mock_enum_member
        mock_site_setting_key.ARCHIVIST_EMAIL = mock_enum_member

        mock_validate_email.side_effect = ValidationError("Invalid email")

        form = SiteSettingModelForm(data={"value": "bad@email"}, instance=self.email_setting)
        self.assertFalse(form.is_valid())
        self.assertIn("ARCHIVIST_EMAIL must be a valid email address.", form.errors["__all__"])
