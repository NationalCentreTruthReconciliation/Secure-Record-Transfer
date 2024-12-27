from caais.models import SourceRole, SourceType
from django.test import TestCase

from recordtransfer.forms import UserProfileForm
from recordtransfer.forms.transfer_forms import SourceInfoForm
from recordtransfer.models import User


class UserProfileFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="old_password",
            gets_notification_emails=True,
        )

    def test_form_valid_data(self):
        form_data = {
            "gets_notification_emails": True,
            "current_password": "old_password",
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("new_password123"))

    def test_form_invalid_current_password(self):
        form_data = {
            "gets_notification_emails": True,
            "current_password": "wrong_password",
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("current_password", form.errors)

    def test_form_new_passwords_do_not_match(self):
        form_data = {
            "current_password": "old_password",
            "new_password": "new_password123",
            "confirm_new_password": "different_password",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_new_password", form.errors)

    def test_form_missing_current_password(self):
        form_data = {
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("current_password", form.errors)

    def test_form_missing_new_password(self):
        form_data = {
            "current_password": "old_password",
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("new_password", form.errors)

    def test_form_missing_confirm_new_password(self):
        form_data = {
            "current_password": "old_password",
            "new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_new_password", form.errors)

    def test_form_new_password_is_same_as_old_password(self):
        form_data = {
            "current_password": "old_password",
            "new_password": "old_password",
            "confirm_new_password": "old_password",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("new_password", form.errors)

    def test_form_empty(self):
        form_data = {}
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("Form is empty.", form.errors["__all__"])

    def test_form_email_notification_initial_false(self):
        self.user.gets_notification_emails = False
        self.user.save()

        form_data = {
            "gets_notification_emails": True,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.gets_notification_emails)

    def test_form_email_notification_initial_true(self):
        form_data = {
            "gets_notification_emails": False,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertFalse(user.gets_notification_emails)

    def test_form_no_changes(self):
        form_data = {
            "gets_notification_emails": True,
            "current_password": "",
            "new_password": "",
            "confirm_new_password": "",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("No fields have been changed.", form.errors["__all__"])


class SourceInfoFormTest(TestCase):
    """Tests the source information form (part of the transfer form)."""

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
                "preliminary_custodial_history": "Preliminary history note.",
            },
            defaults=self.form_defaults,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["source_name"], self.source_name)
        self.assertEqual(form.cleaned_data["source_type"], self.source_type)
        self.assertEqual(form.cleaned_data["source_role"], self.source_role)
        self.assertEqual(form.cleaned_data["source_note"], "")
        self.assertEqual(form.cleaned_data["preliminary_custodial_history"], "")

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
                "preliminary_custodial_history": "History note.",
            },
            defaults=self.form_defaults,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["source_name"], "My Name")
        self.assertEqual(form.cleaned_data["source_type"], new_source_type)
        self.assertEqual(form.cleaned_data["source_role"], new_source_role)
        self.assertEqual(form.cleaned_data["source_note"], "Test Note")
        self.assertEqual(form.cleaned_data["preliminary_custodial_history"], "History note.")

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
                "preliminary_custodial_history": "History note.",
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
        self.assertEqual(form.cleaned_data["preliminary_custodial_history"], "History note.")

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
                "preliminary_custodial_history": "History note.",
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
                "preliminary_custodial_history": "History note.",
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
                "preliminary_custodial_history": "History note.",
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
