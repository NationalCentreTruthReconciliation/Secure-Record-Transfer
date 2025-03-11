from datetime import datetime, timedelta
from typing import Union

from django.test import TestCase

from caais.forms import MetadataForm
from caais.models import Identifier, Metadata


class MetadataFormTest(TestCase):
    """Tests the metadata form which is used for record description."""

    def setUp(self) -> None:
        """Set up the test data."""
        self.form_data: dict[str, Union[str, bool]] = {
            "accession_title": "Test Records",
            "date_of_materials": "2020-01-01",
            "date_is_approximate": False,
            "accession_identifier": "TEST-2020-001",
            "language_of_accession_record": "English",
            "repository": "",
            "acquisition_method": "",
            "status": "",
            "rules_or_conventions": "",
        }

    def test_valid_form(self) -> None:
        """Test that a valid form is accepted."""
        form = MetadataForm(data=self.form_data)
        self.assertEqual(form.errors, {})

    def test_valid_date_range(self) -> None:
        """Test that a date range is accepted."""
        self.form_data["date_of_materials"] = "2020-01-01 - 2020-01-05"
        form = MetadataForm(data=self.form_data)
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
            form = MetadataForm(data=self.form_data)
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
            form = MetadataForm(data=self.form_data)
            self.assertFalse(form.is_valid())
            self.assertIn("Invalid date format", str(form.errors["date_of_materials"]))

    def test_future_start_date(self) -> None:
        """Test that a future start date is rejected."""
        future_date = datetime.now() + timedelta(days=365)
        self.form_data["date_of_materials"] = future_date.strftime(r"%Y-%m-%d")
        form = MetadataForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Date cannot be in the future", str(form.errors["date_of_materials"]))

    def test_future_end_date(self) -> None:
        """Test that a future end date is rejected."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() + timedelta(days=30)
        date_of_materials = (
            start_date.strftime(r"%Y-%m-%d") + " - " + end_date.strftime(r"%Y-%m-%d")
        )
        self.form_data["date_of_materials"] = date_of_materials
        form = MetadataForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("End date cannot be in the future", str(form.errors["date_of_materials"]))

    def test_dates_before_earliest(self) -> None:
        """Test that dates before the earliest date are rejected."""
        self.form_data["date_of_materials"] = "1799-12-31"
        form = MetadataForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Date cannot be before 1800", str(form.errors["date_of_materials"]))

    def test_end_date_before_start_date(self) -> None:
        """Test that an end date before a start date is rejected."""
        self.form_data["date_of_materials"] = "2020-12-31 - 2020-01-01"
        form = MetadataForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("End date must be later than start date", str(form.errors["date_of_materials"]))

    def test_same_start_and_end_date(self) -> None:
        """Test that a start and end date of the same day is accepted.

        If this is the case, the end date is ignored.
        """
        self.form_data["date_of_materials"] = "2020-01-01 - 2020-01-01"
        form = MetadataForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["date_of_materials"], "2020-01-01")

    def test_required_fields(self) -> None:
        """Test that required fields are enforced."""
        required_fields = [
            "accession_title",
            "date_of_materials",
            "accession_identifier",
        ]

        for field in required_fields:
            # Remove the required field
            current_value = self.form_data.pop(field)
            form = MetadataForm(data=self.form_data)
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)
            # Restore the field for the next test
            self.form_data[field] = current_value

    def test_non_required_fields(self) -> None:
        """Test that non-required fields are not enforced."""
        non_required_fields = [
            "acquisition_method",
            "status",
            "repository",
            "rules_or_conventions",
            "language_of_accession_record",
        ]

        for field in non_required_fields:
            # Remove the non-required field
            if field in self.form_data:
                current_value = self.form_data.pop(field)
                form = MetadataForm(data=self.form_data)
                self.assertTrue(form.is_valid(), f"Field {field} is incorrectly marked as required")
                # Restore the field for the next test
                self.form_data[field] = current_value

    def test_accession_identifier_initial_value(self) -> None:
        """Test that the accession identifier field is initialized from instance."""
        metadata = Metadata(accession_title="Test")
        metadata.save()

        identifier = Identifier(
            metadata=metadata,
            identifier_type="Accession Identifier",
            identifier_value="TEST-2021-001",
        )
        identifier.save()

        form = MetadataForm(instance=metadata)
        self.assertEqual(form.fields["accession_identifier"].initial, "TEST-2021-001")

    def test_save_creates_identifier(self) -> None:
        """Test that saving the form creates an Identifier if needed."""
        form = MetadataForm(data=self.form_data)
        self.assertTrue(form.is_valid())

        metadata = form.save()

        # Should have created an Identifier
        self.assertEqual(metadata.accession_identifier, "TEST-2020-001")

        # Check if the identifier exists in the database
        identifier = Identifier.objects.filter(
            metadata=metadata,
            identifier_type="Accession Identifier",
            identifier_value="TEST-2020-001"
        ).first()

        self.assertIsNotNone(identifier)

    def test_save_updates_identifier(self) -> None:
        """Test that saving the form updates an Identifier if it already exists."""
        form = MetadataForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        metadata = form.save()

        # Update the identifier
        updated_data = self.form_data.copy()
        updated_data["accession_identifier"] = "UPDATED-ID-2020"

        update_form = MetadataForm(data=updated_data, instance=metadata)
        self.assertTrue(update_form.is_valid())
        updated_metadata = update_form.save()

        # Should have updated the Identifier
        self.assertEqual(updated_metadata.accession_identifier, "UPDATED-ID-2020")
