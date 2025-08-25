from datetime import datetime, timedelta
from typing import Union

from caais.models import SourceRole, SourceType
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from recordtransfer.forms import UserAccountInfoForm
from recordtransfer.forms.submission_forms import (
    OtherIdentifiersForm,
    RecordDescriptionForm,
    SourceInfoForm,
    UploadFilesForm,
)
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.forms.user_forms import SignUpForm, UserContactInfoForm
from recordtransfer.models import SubmissionGroup, TempUploadedFile, UploadSession, User


class SignUpFormTest(TestCase):
    """Tests for the SignUpForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.valid_form_data = {
            "username": "testuser123",
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password1": "Securepassword123",
            "password2": "Securepassword123",
        }
        self.existing_user = User.objects.create_user(
            username="existinguser",
            first_name="Existing",
            last_name="User",
            email="existing@example.com",
            password="Password123",
        )

    def test_form_save(self) -> None:
        """Test that form saves user correctly with valid data."""
        form = SignUpForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, "testuser123")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertTrue(user.check_password("Securepassword123"))

    def test_form_duplicate_username(self) -> None:
        """Test that form rejects duplicate username."""
        self.valid_form_data["username"] = "existinguser"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_form_duplicate_email(self) -> None:
        """Test that form rejects duplicate email."""
        self.valid_form_data["email"] = "existing@example.com"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_missing_username(self) -> None:
        """Test that form requires username."""
        del self.valid_form_data["username"]
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_form_short_username(self) -> None:
        """Test that form rejects username shorter than 6 characters."""
        self.valid_form_data["username"] = "short"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_form_missing_first_name(self) -> None:
        """Test that form requires first name."""
        del self.valid_form_data["first_name"]
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_form_short_first_name(self) -> None:
        """Test that form rejects first name shorter than 2 characters."""
        self.valid_form_data["first_name"] = "A"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_form_missing_last_name(self) -> None:
        """Test that form requires last name."""
        del self.valid_form_data["last_name"]
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_form_short_last_name(self) -> None:
        """Test that form rejects last name shorter than 2 characters."""
        self.valid_form_data["last_name"] = "B"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_form_missing_email(self) -> None:
        """Test that form requires email."""
        del self.valid_form_data["email"]
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_invalid_email(self) -> None:
        """Test that form rejects invalid email format."""
        self.valid_form_data["email"] = "invalid-email"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_case_sensitive_username_duplicate(self) -> None:
        """Test that a username that differs from an existing username only by case is rejected."""
        self.valid_form_data["username"] = "EXISTINGUSER"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())

    def test_form_case_insensitive_email_duplicate(self) -> None:
        """Test that an email that differs from an existing email only by case is rejected."""
        self.valid_form_data["email"] = "EXISTING@EXAMPLE.COM"
        form = SignUpForm(data=self.valid_form_data)
        self.assertFalse(form.is_valid())


class UserAccountInfoFormTest(TestCase):
    """Tests for the UserAccountInfoForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.test_username = "testuser"
        self.test_first_name = "Test"
        self.test_last_name = "User"
        self.test_email = "testuser@example.com"
        self.test_password = "old_password"
        self.test_gets_notification_emails = True
        self.user = User.objects.create_user(
            username=self.test_username,
            first_name=self.test_first_name,
            last_name=self.test_last_name,
            email=self.test_email,
            password=self.test_password,
            gets_notification_emails=self.test_gets_notification_emails,
        )

    def test_form_valid_name_change(self) -> None:
        """Test that the form can change the user's name successfully."""
        form_data = {
            "first_name": "New",
            "last_name": "Name",
        }
        form = UserAccountInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "Name")

    def test_form_accented_name_change(self) -> None:
        """Test that the form can handle accented characters in names."""
        form_data = {
            "first_name": "Áccéntéd",
            "last_name": "Námé",
        }
        form = UserAccountInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.first_name, "Áccéntéd")
        self.assertEqual(user.last_name, "Námé")

    def test_form_invalid_first_name(self) -> None:
        """Test that the form rejects invalid first names."""
        form_data = {
            "first_name": "123",
            "last_name": self.test_last_name,
        }
        form = UserAccountInfoForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_form_invalid_last_name(self) -> None:
        """Test that the form rejects invalid last names."""
        form_data = {
            "first_name": self.test_first_name,
            "last_name": "123",
        }
        form = UserAccountInfoForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_form_email_notification_initial_false(self) -> None:
        """Test that the form can set email notification preference to False."""
        self.user.gets_notification_emails = False
        self.user.save()

        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": True,
        }
        form = UserAccountInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.gets_notification_emails)

    def test_form_email_notification_initial_true(self) -> None:
        """Test that the form can set email notification preference to True."""
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": False,
        }
        form = UserAccountInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertFalse(user.gets_notification_emails)


class UserContactInfoFormTest(TestCase):
    """Tests for the UserContactInfoForm."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            password="testpassword",
        )
        self.valid_form_data = {
            "phone_number": "+1 (555) 123-4567",
            "address_line_1": "123 Test Street",
            "address_line_2": "Suite 100",
            "city": "Test City",
            "province_or_state": "ON",
            "postal_or_zip_code": "K1A 0A6",
            "country": "CA",
        }

    def test_form_valid_contact_info(self) -> None:
        """Test that the form can save valid contact information."""
        form = UserContactInfoForm(data=self.valid_form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.phone_number, "+1 (555) 123-4567")
        self.assertEqual(user.address_line_1, "123 Test Street")
        self.assertEqual(user.address_line_2, "Suite 100")
        self.assertEqual(user.city, "Test City")
        self.assertEqual(user.province_or_state, "ON")
        self.assertEqual(user.postal_or_zip_code, "K1A 0A6")
        self.assertEqual(user.country, "CA")

    def test_form_valid_without_optional_fields(self) -> None:
        """Test that the form is valid without optional fields."""
        form_data = {
            "phone_number": "+1 (555) 123-4567",
            "address_line_1": "123 Test Street",
            "city": "Test City",
            "province_or_state": "ON",
            "postal_or_zip_code": "K1A 0A6",
            "country": "CA",
        }
        form = UserContactInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_form_invalid_phone_number_format(self) -> None:
        """Test that the form rejects invalid phone number formats."""
        invalid_phone_numbers = [
            "555-1234",
            "(555) 123-4567",
            "1-555-123-4567",
            "+1 555 123 4567",
            "555.123.4567",
        ]

        for phone in invalid_phone_numbers:
            form_data = self.valid_form_data.copy()
            form_data["phone_number"] = phone
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertFalse(form.is_valid())
            self.assertIn("phone_number", form.errors)

    def test_form_valid_phone_number_formats(self) -> None:
        """Test that the form accepts valid phone number formats."""
        valid_phone_numbers = [
            "+1 (555) 123-4567",
            "+1 (800) 555-1234",
            "+1 (123) 456-7890",
        ]

        for phone in valid_phone_numbers:
            form_data = self.valid_form_data.copy()
            form_data["phone_number"] = phone
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self) -> None:
        """Test that the form requires all mandatory fields."""
        required_fields = [
            "phone_number",
            "address_line_1",
            "city",
            "province_or_state",
            "postal_or_zip_code",
            "country",
        ]

        for field in required_fields:
            form_data = self.valid_form_data.copy()
            del form_data[field]
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)

    def test_form_invalid_postal_code_formats(self) -> None:
        """Test that the form rejects invalid postal/zip code formats."""
        invalid_postal_codes = [
            "K1A  0A6",  # Canadian postal code with double space
            "ABCDEF",  # All letters
        ]

        for postal_code in invalid_postal_codes:
            form_data = self.valid_form_data.copy()
            form_data["postal_or_zip_code"] = postal_code
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertFalse(form.is_valid())
            self.assertIn("postal_or_zip_code", form.errors)

    def test_form_valid_postal_code_formats(self) -> None:
        """Test that the form accepts valid postal/zip code formats."""
        valid_postal_codes = [
            "K1A 0A6",  # Canadian postal code with space
            "K1A0A6",  # Canadian postal code without space
            "12345",  # US zip code
            "12345-1234",  # US zip+4 code
        ]

        for postal_code in valid_postal_codes:
            form_data = self.valid_form_data.copy()
            form_data["postal_or_zip_code"] = postal_code
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertTrue(form.is_valid())

    def test_form_other_province_or_state(self) -> None:
        """Test that the form handles 'Other' province/state selection."""
        # Test that 'Other' requires other_province_or_state field
        form_data = self.valid_form_data.copy()
        form_data["province_or_state"] = "Other"
        form_data["other_province_or_state"] = ""
        form = UserContactInfoForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("other_province_or_state", form.errors)

        # Test that 'Other' with other_province_or_state is valid
        form_data["other_province_or_state"] = "Custom Province"
        form = UserContactInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_form_address_line_2_without_line_1(self) -> None:
        """Test that address line 2 requires address line 1."""
        form_data = self.valid_form_data.copy()
        form_data["address_line_1"] = ""
        form_data["address_line_2"] = "Suite 100"
        form = UserContactInfoForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("address_line_1", form.errors)

    def test_form_clears_other_province_when_not_other(self) -> None:
        """Test that other_province_or_state is cleared when not selecting 'Other'."""
        form_data = self.valid_form_data.copy()
        form_data["province_or_state"] = "ON"
        form_data["other_province_or_state"] = "Should be cleared"
        form = UserContactInfoForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        # The form should clear the other_province_or_state field
        self.assertEqual(form.cleaned_data["other_province_or_state"], "")

    def test_form_empty_data(self) -> None:
        """Test that the form is invalid with empty data."""
        form = UserContactInfoForm(data={}, instance=self.user)
        self.assertFalse(form.is_valid())
        # Should have errors for all required fields
        required_fields = [
            "phone_number",
            "address_line_1",
            "city",
            "province_or_state",
            "postal_or_zip_code",
            "country",
        ]
        for field in required_fields:
            self.assertIn(field, form.errors)

    def test_form_canadian_provinces(self) -> None:
        """Test that Canadian provinces are accepted."""
        canadian_provinces = [
            "AB",
            "BC",
            "MB",
            "NB",
            "NL",
            "NS",
            "NT",
            "NU",
            "ON",
            "PE",
            "QC",
            "SK",
            "YT",
        ]

        for province in canadian_provinces:
            form_data = self.valid_form_data.copy()
            form_data["province_or_state"] = province
            form_data["postal_or_zip_code"] = "K1A 0A6"  # Canadian postal code
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertTrue(form.is_valid())

    def test_form_us_states(self) -> None:
        """Test that US states are accepted."""
        us_states = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

        for state in us_states:
            form_data = self.valid_form_data.copy()
            form_data["province_or_state"] = state
            form_data["postal_or_zip_code"] = "12345"  # US zip code
            form = UserContactInfoForm(data=form_data, instance=self.user)
            self.assertTrue(form.is_valid())


class RecordDescriptionFormTest(TestCase):
    """Tests the RecordDescriptionForm (part of the submission form)."""

    def setUp(self) -> None:
        """Set up the test data."""
        self.form_data: dict[str, Union[str, bool]] = {
            "accession_title": "Test Records",
            "date_of_materials": "2020-01-01",
            "language_of_material": "English",
            "preliminary_scope_and_content": "Test content description",
            "preliminary_custodial_history": "History note.",
        }

    def test_valid_single_date(self) -> None:
        """Test that a single yyyy-mm-dd date is accepted."""
        form = RecordDescriptionForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_valid_date_range(self) -> None:
        """Test that a date range is accepted."""
        self.form_data["date_of_materials"] = "2020-01-01 - 2020-01-05"
        form = RecordDescriptionForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_date_format(self) -> None:
        """Test that invalid date formats are rejected."""
        invalid_formats = [
            "01-01-2020",
            "2020/01/01",
            "2020-1-1",
            "2020-00-00",
            "2020.01.01",
            "01/01/2020 - 12/31/2020",
        ]
        for date_format in invalid_formats:
            self.form_data["date_of_materials"] = date_format
            form = RecordDescriptionForm(data=self.form_data)
            self.assertFalse(form.is_valid())
            self.assertIn("date_of_materials", form.errors)

    def test_invalid_month_day_combinations(self) -> None:
        """Test that invalid month-day combinations are rejected."""
        invalid_dates = [
            "2020-02-30",  # Invalid February date
            "2020-04-31",  # April has 30 days
            "2020-06-31",  # June has 30 days
            "2020-09-31",  # September has 30 days
            "2020-11-31",  # November has 30 days
        ]
        for date in invalid_dates:
            self.form_data["date_of_materials"] = date
            form = RecordDescriptionForm(data=self.form_data)
            self.assertFalse(form.is_valid())
            self.assertIn("Invalid date format", form.errors["date_of_materials"])

    def test_future_start_date(self) -> None:
        """Test that a future start date is rejected."""
        future_date = datetime.now() + timedelta(days=365)
        self.form_data["date_of_materials"] = future_date.strftime(r"%Y-%m-%d")
        form = RecordDescriptionForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Date cannot be in the future", form.errors["date_of_materials"])

    def test_future_end_date(self) -> None:
        """Test that a future end date is rejected."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() + timedelta(days=30)
        date_of_materials = (
            start_date.strftime(r"%Y-%m-%d") + " - " + end_date.strftime(r"%Y-%m-%d")
        )
        self.form_data["date_of_materials"] = date_of_materials
        form = RecordDescriptionForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("End date cannot be in the future", form.errors["date_of_materials"])

    def test_dates_before_earliest(self) -> None:
        """Test that dates before the earliest date are rejected."""
        self.form_data["date_of_materials"] = "1799-12-31"
        form = RecordDescriptionForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Date cannot be before 1800", form.errors["date_of_materials"])

    def test_end_date_before_start_date(self) -> None:
        """Test that an end date before a start date is rejected."""
        self.form_data["date_of_materials"] = "2020-12-31 - 2020-01-01"
        form = RecordDescriptionForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("End date must be later than start date", form.errors["date_of_materials"])

    def test_same_start_and_end_date(self) -> None:
        """Test that a start and end date of the same day is accepted.

        If this is the case, the end date is ignored.
        """
        self.form_data["date_of_materials"] = "2020-01-01 - 2020-01-01"
        form = RecordDescriptionForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["date_of_materials"], "2020-01-01")


class SourceInfoFormTest(TestCase):
    """Tests the SourceInformationForm (part of the submission form)."""

    def setUp(self) -> None:
        """Create initial test data."""
        self.source_name = "Person Name"
        self.source_type = SourceType.objects.get_or_create(name="Test Source Type")[0]
        self.source_role = SourceRole.objects.get_or_create(name="Test Source Role")[0]
        self.form_defaults = {
            "source_type": self.source_type,
            "source_role": self.source_role,
            "source_name": self.source_name,
        }

    def test_defaults_not_manual(self) -> None:
        """Case where the user skips the form and does not enter any data."""
        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "no",
            },
            defaults=self.form_defaults,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["source_name"], self.source_name)
        self.assertEqual(form.cleaned_data["source_type"], self.source_type)
        self.assertEqual(form.cleaned_data["source_role"], self.source_role)

    def test_data_overwritten_not_manual(self) -> None:
        """Case where some info is entered manually, but then the user decides to skip the form."""
        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "no",
                "source_name": "My New Name",
                "source_note": "This is a test note that will be overwritten.",
            },
            defaults=self.form_defaults,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["source_name"], self.source_name)
        self.assertEqual(form.cleaned_data["source_type"], self.source_type)
        self.assertEqual(form.cleaned_data["source_role"], self.source_role)
        self.assertEqual(form.cleaned_data["source_note"], "")

    def test_valid_manual_source_info(self) -> None:
        """Case where the user manually enters valid source information."""
        new_source_type = SourceType.objects.get_or_create(name="New Source Type")[0]
        new_source_role = SourceRole.objects.get_or_create(name="New Source Role")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "My Name",
                "source_type": new_source_type.pk,
                "source_role": new_source_role.pk,
                "source_note": "Test Note",
            },
            defaults=self.form_defaults,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["source_name"], "My Name")
        self.assertEqual(form.cleaned_data["source_type"], new_source_type)
        self.assertEqual(form.cleaned_data["source_role"], new_source_role)
        self.assertEqual(form.cleaned_data["source_note"], "Test Note")

    def test_valid_manual_source_info_with_other(self) -> None:
        """Case where the user manually enters valid source information including Other fields."""
        other_source_type = SourceType.objects.get_or_create(name="Other")[0]
        other_source_role = SourceRole.objects.get_or_create(name="Other")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "My Name",
                "source_type": other_source_type.pk,
                "other_source_type": "My Other Source Type",
                "source_role": other_source_role.pk,
                "other_source_role": "My Other Source Role",
                "source_note": "Test Note",
            },
            defaults=self.form_defaults,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["source_name"], "My Name")
        self.assertEqual(form.cleaned_data["source_type"], other_source_type)
        self.assertEqual(form.cleaned_data["other_source_type"], "My Other Source Type")
        self.assertEqual(form.cleaned_data["source_role"], other_source_role)
        self.assertEqual(form.cleaned_data["other_source_role"], "My Other Source Role")
        self.assertEqual(form.cleaned_data["source_note"], "Test Note")

    def test_invalid_name(self) -> None:
        """Case where the user forgot to specify a name."""
        new_source_type = SourceType.objects.get_or_create(name="New Source Type")[0]
        new_source_role = SourceRole.objects.get_or_create(name="New Source Role")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "",
                "source_type": new_source_type.pk,
                "source_role": new_source_role.pk,
                "source_note": "Test Note",
            },
            defaults=self.form_defaults,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(1, len(form.errors))
        self.assertIn("source_name", form.errors)

    def test_invalid_source_type(self) -> None:
        """Case where the user forgot to specify a source type."""
        new_source_role = SourceRole.objects.get_or_create(name="New Source Role")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "My Name",
                "source_type": None,
                "source_role": new_source_role.pk,
                "source_note": "Test Note",
            },
            defaults=self.form_defaults,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(1, len(form.errors))
        self.assertIn("source_type", form.errors)

    def test_invalid_source_role(self) -> None:
        """Case where the user forgot to specify a source role."""
        new_source_type = SourceType.objects.get_or_create(name="New Source Type")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "My Name",
                "source_type": new_source_type.pk,
                "source_role": None,
                "source_note": "Test Note",
            },
            defaults=self.form_defaults,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(1, len(form.errors))
        self.assertIn("source_role", form.errors)

    def test_other_source_type_missing(self) -> None:
        """Case when the user forgets to write an 'Other' source type."""
        other_type = SourceType.objects.get_or_create(name="Other")[0]
        new_source_role = SourceRole.objects.get_or_create(name="New Source Role")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "My Name",
                "source_type": other_type.pk,
                "source_role": new_source_role.pk,
            },
            defaults=self.form_defaults,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(1, len(form.errors))
        self.assertIn("other_source_type", form.errors)

    def test_other_source_role_missing(self) -> None:
        """Case when the user forgets to write an 'Other' source role."""
        new_source_type = SourceType.objects.get_or_create(name="New Source Type")[0]
        other_role = SourceRole.objects.get_or_create(name="Other")[0]

        form = SourceInfoForm(
            data={
                "enter_manual_source_info": "yes",
                "source_name": "My Name",
                "source_type": new_source_type.pk,
                "source_role": other_role.pk,
            },
            defaults=self.form_defaults,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(1, len(form.errors))
        self.assertIn("other_source_role", form.errors)


class OtherIdentifiersFormTest(TestCase):
    """Tests for the OtherIdentifiersForm."""

    def test_form_valid_with_all_fields(self) -> None:
        """Test that the form is valid when all fields are provided."""
        form_data = {
            "other_identifier_type": "Receipt number",
            "other_identifier_value": "12345",
            "other_identifier_note": "This is a test note",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["other_identifier_type"], "Receipt number")
        self.assertEqual(form.cleaned_data["other_identifier_value"], "12345")
        self.assertEqual(form.cleaned_data["other_identifier_note"], "This is a test note")

    def test_form_valid_with_type_and_value_only(self) -> None:
        """Test that the form is valid when only type and value are provided."""
        form_data = {
            "other_identifier_type": "LAC Record ID",
            "other_identifier_value": "ABC-123",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["other_identifier_type"], "LAC Record ID")
        self.assertEqual(form.cleaned_data["other_identifier_value"], "ABC-123")
        self.assertEqual(form.cleaned_data["other_identifier_note"], "")

    def test_form_valid_with_empty_fields(self) -> None:
        """Test that the form is valid when all fields are empty."""
        form_data = {
            "other_identifier_type": "",
            "other_identifier_value": "",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_type_without_value(self) -> None:
        """Test that the form is invalid when type is provided but value is missing."""
        form_data = {
            "other_identifier_type": "Receipt number",
            "other_identifier_value": "",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_value", form.errors)
        self.assertIn(
            "Must enter a value for this identifier", form.errors["other_identifier_value"]
        )

    def test_form_invalid_value_without_type(self) -> None:
        """Test that the form is invalid when value is provided but type is missing."""
        form_data = {
            "other_identifier_type": "",
            "other_identifier_value": "12345",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_type", form.errors)
        self.assertIn(
            "Must enter a type for this identifier", form.errors["other_identifier_type"]
        )

    def test_form_invalid_note_without_type_and_value(self) -> None:
        """Test that the form is invalid when note is provided but type and value are missing."""
        form_data = {
            "other_identifier_type": "",
            "other_identifier_value": "",
            "other_identifier_note": "This is a test note",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_type", form.errors)
        self.assertIn("other_identifier_value", form.errors)
        self.assertIn("other_identifier_note", form.errors)
        self.assertIn(
            "Must enter a type for this identifier", form.errors["other_identifier_type"]
        )
        self.assertIn(
            "Must enter a value for this identifier", form.errors["other_identifier_value"]
        )
        self.assertIn(
            "Cannot enter a note without entering a value and type",
            form.errors["other_identifier_note"],
        )

    def test_form_invalid_type_and_note_without_value(self) -> None:
        """Test that the form is invalid when type and note are provided but value is missing."""
        form_data = {
            "other_identifier_type": "Receipt number",
            "other_identifier_value": "",
            "other_identifier_note": "This is a test note",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_value", form.errors)
        self.assertIn(
            "Must enter a value for this identifier", form.errors["other_identifier_value"]
        )

    def test_form_invalid_value_and_note_without_type(self) -> None:
        """Test that the form is invalid when value and note are provided but type is missing."""
        form_data = {
            "other_identifier_type": "",
            "other_identifier_value": "12345",
            "other_identifier_note": "This is a test note",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_type", form.errors)
        self.assertIn(
            "Must enter a type for this identifier", form.errors["other_identifier_type"]
        )

    def test_form_field_labels_and_placeholders(self) -> None:
        """Test that form fields have correct labels and placeholders."""
        form = OtherIdentifiersForm()

        # Test labels
        self.assertEqual(form.fields["other_identifier_type"].label, "Type of identifier")
        self.assertEqual(form.fields["other_identifier_value"].label, "Identifier value")
        self.assertEqual(form.fields["other_identifier_note"].label, "Notes for identifier")

        # Test placeholders
        self.assertEqual(
            form.fields["other_identifier_type"].widget.attrs["placeholder"],
            "The type of the identifier",
        )
        self.assertEqual(
            form.fields["other_identifier_value"].widget.attrs["placeholder"], "Identifier value"
        )
        self.assertEqual(
            form.fields["other_identifier_note"].widget.attrs["placeholder"],
            "Any notes on this identifier or which files it may apply to (optional).",
        )

    def test_form_field_required_attributes(self) -> None:
        """Test that all form fields are correctly marked as not required."""
        form = OtherIdentifiersForm()

        self.assertFalse(form.fields["other_identifier_type"].required)
        self.assertFalse(form.fields["other_identifier_value"].required)
        self.assertFalse(form.fields["other_identifier_note"].required)

    def test_form_field_widgets(self) -> None:
        """Test that form fields have correct widget types."""
        form = OtherIdentifiersForm()

        self.assertIsInstance(form.fields["other_identifier_type"].widget, forms.TextInput)
        self.assertIsInstance(form.fields["other_identifier_value"].widget, forms.TextInput)
        self.assertIsInstance(form.fields["other_identifier_note"].widget, forms.Textarea)

        # Test textarea rows attribute
        self.assertEqual(form.fields["other_identifier_note"].widget.attrs["rows"], "2")

    def test_form_invalid_reserved_type_accession_number(self) -> None:
        """Test that the form rejects 'Accession Number' as a reserved identifier type."""
        form_data = {
            "other_identifier_type": "Accession Number",
            "other_identifier_value": "12345",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_type", form.errors)
        self.assertIn(
            "This identifier type is reserved and cannot be used",
            form.errors["other_identifier_type"],
        )

    def test_form_invalid_reserved_type_accession_identifier(self) -> None:
        """Test that the form rejects 'Accession Identifier' as a reserved identifier type."""
        form_data = {
            "other_identifier_type": "Accession Identifier",
            "other_identifier_value": "12345",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_type", form.errors)
        self.assertIn(
            "This identifier type is reserved and cannot be used",
            form.errors["other_identifier_type"],
        )

    def test_form_invalid_reserved_type_case_insensitive(self) -> None:
        """Test that reserved identifier type validation is case insensitive."""
        test_cases = [
            "ACCESSION NUMBER",
            "accession number",
            "Accession Number",
            "aCcEsSiOn NuMbEr",
            "ACCESSION IDENTIFIER",
            "accession identifier",
            "Accession Identifier",
            "aCcEsSiOn IdEnTiFiEr",
        ]

        for reserved_type in test_cases:
            with self.subTest(reserved_type=reserved_type):
                form_data = {
                    "other_identifier_type": reserved_type,
                    "other_identifier_value": "12345",
                    "other_identifier_note": "",
                }
                form = OtherIdentifiersForm(data=form_data)
                self.assertFalse(form.is_valid())
                self.assertIn("other_identifier_type", form.errors)
                self.assertIn(
                    "This identifier type is reserved and cannot be used",
                    form.errors["other_identifier_type"],
                )

    def test_form_valid_similar_but_not_reserved_types(self) -> None:
        """Test that similar but non-reserved identifier types are allowed."""
        valid_similar_types = [
            "Accession Numbers",  # Plural
            "My Accession Number",  # With prefix
            "Accession Number Copy",  # With suffix
            "Accession ID",  # Different but similar
            "Access Number",  # Similar spelling
            "Record Number",  # Different type
        ]

        for valid_type in valid_similar_types:
            with self.subTest(valid_type=valid_type):
                form_data = {
                    "other_identifier_type": valid_type,
                    "other_identifier_value": "12345",
                    "other_identifier_note": "",
                }
                form = OtherIdentifiersForm(data=form_data)
                self.assertTrue(form.is_valid(), f"Form should be valid for type: {valid_type}")

    def test_form_reserved_type_error_with_missing_value(self) -> None:
        """Test that reserved type error is shown even when value is missing."""
        form_data = {
            "other_identifier_type": "Accession Number",
            "other_identifier_value": "",
            "other_identifier_note": "",
        }
        form = OtherIdentifiersForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("other_identifier_type", form.errors)
        self.assertIn("other_identifier_value", form.errors)
        self.assertIn(
            "This identifier type is reserved and cannot be used",
            form.errors["other_identifier_type"],
        )
        self.assertIn(
            "Must enter a value for this identifier", form.errors["other_identifier_value"]
        )


class UploadFilesFormTest(TestCase):
    """Tests for the UploadFilesForm."""

    def setUp(self) -> None:
        """Create a test session and include one uploaded file as part of session."""
        self.upload_session = UploadSession.new_session()
        self.uploaded_file = TempUploadedFile.objects.create(
            session=self.upload_session,
            file_upload=SimpleUploadedFile("test_file.txt", bytearray([1] * (1024**2))),
            name="test_file.txt",
        )
        self.uploaded_file.save()

    def test_form_valid(self) -> None:
        """Case where the form is valid."""
        form_data = {
            "session_token": self.upload_session.token,
            "general_note": "Some general note",
        }
        form = UploadFilesForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["quantity_and_unit_of_measure"],
            self.upload_session.get_quantity_and_unit_of_measure(),
        )

    def test_form_missing_session_token(self) -> None:
        """Case where the session token is missing."""
        form_data = {
            "general_note": "Some general note",
        }
        form = UploadFilesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("session_token", form.errors)

    def test_form_invalid_session_token(self) -> None:
        """Case where the session token is invalid."""
        form_data = {
            "session_token": "invalidtoken",
            "general_note": "Some general note",
        }
        form = UploadFilesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("session_token", form.errors)

    def test_form_no_files_uploaded(self) -> None:
        """Case where no files have been uploaded."""
        self.uploaded_file.delete()
        form_data = {
            "session_token": self.upload_session.token,
            "general_note": "Some general note",
        }
        form = UploadFilesForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("session_token", form.errors)


class SubmissionGroupFormTest(TestCase):
    """Tests for the SubmissionGroupForm."""

    def setUp(self) -> None:
        """Create initial test data."""
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.existing_group = SubmissionGroup.objects.create(
            name="Existing Group", description="An existing submission group", created_by=self.user
        )

    def test_form_valid_data(self) -> None:
        """Case where the form is valid."""
        form_data = {"name": "New Group", "description": "A new submission group"}
        form = SubmissionGroupForm(data=form_data, user=self.user)
        assert form.is_valid()
        group = form.save()
        self.assertEqual(group.name, "New Group")
        self.assertEqual(group.description, "A new submission group")
        self.assertEqual(group.created_by, self.user)

    def test_form_empty_data(self) -> None:
        """Case where the form is empty."""
        form = SubmissionGroupForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())

    def test_form_missing_name(self) -> None:
        """Case where the name is missing."""
        form_data = {"description": "A new submission group"}
        form = SubmissionGroupForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_form_duplicate_name(self) -> None:
        """Case where the name is a duplicate of an existing group name."""
        form_data = {"name": "Existing Group", "description": "A duplicate submission group"}
        form = SubmissionGroupForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_form_no_changes(self) -> None:
        """Case where no changes are detected."""
        form_data = {"name": "Existing Group", "description": "A new description"}
        form = SubmissionGroupForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_form_save(self) -> None:
        """Case where the form is saved."""
        form_data = {"name": "New Group", "description": "A new submission group"}
        form = SubmissionGroupForm(data=form_data, instance=self.existing_group, user=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        self.existing_group.refresh_from_db()
        self.assertEqual(self.existing_group.name, "New Group")
        self.assertEqual(self.existing_group.description, "A new submission group")
        self.assertEqual(self.existing_group.created_by, self.user)

    def test_form_invalid_fields(self) -> None:
        """Case where the form is passed fields that are not allowed to be modified."""
        original_created_by = self.existing_group.created_by
        original_uuid = self.existing_group.uuid
        different_user = User.objects.create_user(username="differentuser", password="12345")
        form_data = {
            "name": "New Group",
            "description": "A new submission group",
            "created_by": different_user,
            "uuid": "12345",
        }
        form = SubmissionGroupForm(data=form_data, instance=self.existing_group, user=self.user)
        form.save()
        self.existing_group.refresh_from_db()
        # Check that the fields were not modified
        self.assertEqual(self.existing_group.created_by, original_created_by)
        self.assertEqual(self.existing_group.uuid, original_uuid)
