from caais.models import SourceRole, SourceType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from recordtransfer.forms import UserProfileForm
from recordtransfer.forms.submission_group_form import SubmissionGroupForm
from recordtransfer.forms.transfer_forms import SourceInfoForm, UploadFilesForm
from recordtransfer.models import SubmissionGroup, TempUploadedFile, UploadSession, User


class UserProfileFormTest(TestCase):
    def setUp(self):
        self.test_username = "testuser"
        self.test_first_name = "Test"
        self.test_last_name = "User"
        self.test_email = "testuser@example.com"
        self.test_password = "old_password"
        self.test_gets_notification_emails = True
        self.test_new_password = "new_password123"
        self.user = User.objects.create_user(
            username=self.test_username,
            first_name=self.test_first_name,
            last_name=self.test_last_name,
            email=self.test_email,
            password=self.test_password,
            gets_notification_emails=self.test_gets_notification_emails,
        )

    def test_form_valid_name_change(self):
        form_data = {
            "first_name": "New",
            "last_name": "Name",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "Name")

    def test_form_accented_name_change(self):
        form_data = {
            "first_name": "Áccéntéd",
            "last_name": "Námé",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.first_name, "Áccéntéd")
        self.assertEqual(user.last_name, "Námé")

    def test_form_invalid_first_name(self):
        form_data = {
            "first_name": "123",
            "last_name": self.test_last_name,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_form_invalid_last_name(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": "123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_form_valid_password_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_password,
            "new_password": self.test_new_password,
            "confirm_new_password": self.test_new_password,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("new_password123"))

    def test_form_invalid_current_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": "wrong_password",
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("current_password", form.errors)

    def test_form_new_passwords_do_not_match(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_password,
            "new_password": "new_password123",
            "confirm_new_password": "different_password",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_new_password", form.errors)

    def test_form_missing_current_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("current_password", form.errors)

    def test_form_missing_new_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_password,
            "confirm_new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("new_password", form.errors)

    def test_form_missing_confirm_new_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_password,
            "new_password": "new_password123",
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("confirm_new_password", form.errors)

    def test_form_new_password_is_same_as_old_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_password,
            "new_password": self.test_password,
            "confirm_new_password": self.test_password,
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
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": True,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.gets_notification_emails)

    def test_form_email_notification_initial_true(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": False,
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertFalse(user.gets_notification_emails)

    def test_form_no_changes(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": self.test_gets_notification_emails,
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
