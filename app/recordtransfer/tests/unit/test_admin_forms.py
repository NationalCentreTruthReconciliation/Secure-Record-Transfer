"""Tests for admin forms."""

from django.test import TestCase

from recordtransfer.forms.admin_forms import UserAdminForm
from recordtransfer.models import User


class TestUserAdminForm(TestCase):
    """Tests for the UserAdminForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpassword123",
        )

    def test_contact_fields_not_required_by_default(self) -> None:
        """Test that contact info fields are not required for admin form."""
        form = UserAdminForm(instance=self.user)
        contact_fields = [
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "province_or_state",
            "other_province_or_state",
            "postal_or_zip_code",
            "country",
        ]

        for field_name in contact_fields:
            self.assertFalse(form.fields[field_name].required)

    def test_valid_with_no_contact_info(self) -> None:
        """Test that form is valid with no contact information."""
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
        }
        form = UserAdminForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_with_complete_contact_info(self) -> None:
        """Test that form is valid with complete contact information."""
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone_number": "+1 (555) 123-4567",
            "address_line_1": "123 Test Street",
            "city": "Test City",
            "province_or_state": "ON",
            "postal_or_zip_code": "K1A 0A6",
            "country": "CA",
        }
        form = UserAdminForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_with_partial_contact_info(self) -> None:
        """Test that form is invalid when some but not all contact fields are provided."""
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone_number": "+1 (555) 123-4567",
            "address_line_1": "123 Test Street",
            # Missing city, province_or_state, postal_or_zip_code, country
        }
        form = UserAdminForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())

        # Check that missing required fields have errors
        self.assertIn("city", form.errors)
        self.assertIn("province_or_state", form.errors)
        self.assertIn("postal_or_zip_code", form.errors)
        self.assertIn("country", form.errors)

    def test_valid_with_optional_fields(self) -> None:
        """Test that form is valid with optional contact fields included."""
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone_number": "+1 (555) 123-4567",
            "address_line_1": "123 Test Street",
            "address_line_2": "Unit 100",  # Optional field
            "city": "Test City",
            "province_or_state": "ON",
            "postal_or_zip_code": "K1A 0A6",
            "country": "CA",
        }
        form = UserAdminForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_other_province_validation(self) -> None:
        """Test validation when 'Other' province is selected."""
        form_data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone_number": "+1 (555) 123-4567",
            "address_line_1": "123 Test Street",
            "city": "Test City",
            "province_or_state": "Other",
            "postal_or_zip_code": "12345",
            "country": "US",
        }

        # Should be invalid without other_province_or_state
        form = UserAdminForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("other_province_or_state", form.errors)

        # Should be valid with other_province_or_state filled
        form_data["other_province_or_state"] = "Custom Province"
        form = UserAdminForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
