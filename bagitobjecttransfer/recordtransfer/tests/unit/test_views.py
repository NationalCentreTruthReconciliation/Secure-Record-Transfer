import logging
from unittest import skipIf
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext
from override_storage import override_storage
from override_storage.storage import LocMemStorage

from recordtransfer.models import UploadedFile, UploadSession, User


class TestHomepage(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    def test_index(self):
        response = self.client.get(reverse("recordtransfer:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome")


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE", 3)  # MiB
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE", 1)  # MiB
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
@override_storage(storage=LocMemStorage())
class TestUploadFileView(TestCase):
    """Tests for recordtransfer:uploadfile view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls):
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = User.objects.create_user(username="testuser1", password="1X<ISRUkw+tuK")

    def setUp(self):
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.patch__accept_file = patch("recordtransfer.views.accept_file").start()
        self.patch__accept_session = patch("recordtransfer.views.accept_session").start()
        self.patch_check_for_malware = patch("recordtransfer.views.check_for_malware").start()
        self.patch__accept_file.return_value = {"accepted": True}
        self.patch__accept_session.return_value = {"accepted": True}

    def test_logged_out_error(self):
        self.client.logout()
        response = self.client.post(reverse("recordtransfer:uploadfile"), {})
        self.assertEqual(response.status_code, 302)

    def test_500_error_caught(self):
        self.patch__accept_file.side_effect = ValueError("err")
        response = self.client.post(
            reverse("recordtransfer:uploadfile"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )
        self.assertEqual(response.status_code, 500)

    def test_no_files_uploaded(self):
        response = self.client.post(reverse("recordtransfer:uploadfile"), {})
        self.assertEqual(response.status_code, 400)

    def test_new_session_created(self):
        response = self.client.post(
            reverse("recordtransfer:uploadfile"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn("uploadSessionToken", response_json)
        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()
        self.assertTrue(session)

        session.uploadedfile_set.all().delete()
        session.delete()

    def test_same_session_used(self):
        session = UploadSession.new_session()
        session.save()

        response = self.client.post(
            reverse("recordtransfer:uploadfile"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            headers={"upload-session-token": session.token},
        )

        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["uploadSessionToken"], session.token)
        self.assertEqual(len(session.uploadedfile_set.all()), 1)
        self.assertEqual(session.uploadedfile_set.first().name, "File.PDF")

        session.uploadedfile_set.all().delete()
        session.delete()

    def test_file_issue_flagged(self):
        self.patch__accept_file.return_value = {"accepted": False, "error": "ISSUE"}

        response = self.client.post(
            reverse("recordtransfer:uploadfile"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        response_json = response.json()

        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(response_json["uploadSessionToken"])

        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "ISSUE")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(len(session.uploadedfile_set.all()), 0)

        session.uploadedfile_set.all().delete()
        session.delete()

    def test_session_issue_flagged(self):
        self.patch__accept_session.return_value = {"accepted": False, "error": "ISSUE"}

        response = self.client.post(
            reverse("recordtransfer:uploadfile"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        response_json = response.json()

        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(response_json["uploadSessionToken"])

        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "ISSUE")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(len(session.uploadedfile_set.all()), 0)

        session.uploadedfile_set.all().delete()
        session.delete()

    def test_malware_flagged(self):
        self.patch_check_for_malware.side_effect = ValidationError("Malware found")
        response = self.client.post(
            reverse("recordtransfer:uploadfile"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        response_json = response.json()

        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(response_json["uploadSessionToken"])

        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), 'Malware was detected in the file "File.PDF"')
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(len(session.uploadedfile_set.all()), 0)

        session.uploadedfile_set.all().delete()
        session.delete()

    @skipIf(True, "File content scanning is not implemented yet")
    def test_content_issue_flagged(self):
        """
        self.patch__accept_contents.return_value = {
            "accepted": False,
            "error": "ISSUE",
            "clamav": {
                "reason": "Virus",
                "status": "FOUND",
            },
        }
        """

    def tearDown(self):
        self.client.logout()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        logging.disable(logging.NOTSET)
        patch.stopall()
        UploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()


class TestMediaRequestView(TestCase):
    """Test the recordtransfer:media view."""

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Create user accounts."""
        cls.non_admin_user = User.objects.create_user(
            username="non-admin", password="1X<ISRUkw+tuK"
        )
        cls.staff_user = User.objects.create_user(
            username="admin", password="3&SAjfTYZQ", is_staff=True
        )

    def test_302_returned_logged_out(self) -> None:
        """Check that 302 is returned if the client is logged out.

        A 302 is returned because of the login_required() validator.
        """
        uri = reverse("recordtransfer:media", kwargs={"path": "test.txt"})

        response = self.client.get(uri)

        self.assertEqual(response.status_code, 302)

    def test_403_returned_not_staff(self) -> None:
        """Check that 403 is returned if the user is not staff."""
        self.client.login(username="non-admin", password="1X<ISRUkw+tuK")
        uri = reverse("recordtransfer:media", kwargs={"path": "test.txt"})

        response = self.client.get(uri)

        self.assertEqual(response.status_code, 403)

    def test_200_returned_staff(self) -> None:
        """Check that 200 is returned if the user is staff."""
        self.client.login(username="admin", password="3&SAjfTYZQ")
        uri = reverse("recordtransfer:media", kwargs={"path": "test.txt"})

        response = self.client.get(uri)

        self.assertTrue(response.has_header("X-Accel-Redirect"))
        self.assertFalse(response.has_header("Content-Type"))
        self.assertEqual(response.status_code, 200)


class TestListUploadedFilesView(TestCase):
    """Tests for recordtransfer:list_uploaded_files view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls):
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = User.objects.create_user(username="testuser1", password="1X<ISRUkw+tuK")

    def setUp(self):
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.session = UploadSession.new_session()
        self.session.save()
        self.url = reverse("recordtransfer:list_uploaded_files", args=[self.session.token])

    def test_list_uploaded_files_session_not_found(self):
        """Invalid session token."""
        response = self.client.get(
            reverse("recordtransfer:list_uploaded_files", args=["invalid_token"])
        )
        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertIn("error", response_json)

    def test_list_uploaded_files_empty_session(self):
        """Session has no files."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json.get("files"), [])

    def test_list_uploaded_files_with_files(self):
        """Session has one file."""
        uploaded_file = UploadedFile(
            session=self.session,
            file_upload=SimpleUploadedFile("testfile.txt", self.one_kib),
            name="testfile.txt",
        )
        uploaded_file.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        responseFiles = response_json.get("files")
        self.assertEqual(len(responseFiles), 1)
        self.assertEqual(responseFiles[0]["name"], "testfile.txt")
        self.assertEqual(responseFiles[0]["size"], uploaded_file.file_upload.size)
        self.assertEqual(responseFiles[0]["url"], uploaded_file.get_file_access_url())

    def tearDown(self):
        UploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()


class TestUploadedFileView(TestCase):
    """Tests for recordtransfer:uploaded_file view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls):
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = User.objects.create_user(username="testuser1", password="1X<ISRUkw+tuK")

    def setUp(self):
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.session = UploadSession.new_session()
        self.session.save()
        self.uploaded_file = UploadedFile(
            session=self.session,
            file_upload=SimpleUploadedFile("testfile.txt", self.one_kib),
            name="testfile.txt",
        )
        self.uploaded_file.save()
        self.url = reverse(
            "recordtransfer:uploaded_file", args=[self.session.token, self.uploaded_file.name]
        )

    def test_uploaded_file_session_not_found(self):
        """Invalid session token."""
        response = self.client.get(
            reverse("recordtransfer:uploaded_file", args=["invalid_token", "testfile.txt"])
        )
        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertIn("error", response_json)
        self.assertEqual(response_json["error"], gettext("Upload session not found"))

    def test_uploaded_file_not_found(self):
        """Invalid file name in a valid session."""
        response = self.client.get(
            reverse("recordtransfer:uploaded_file", args=[self.session.token, "invalid_file.txt"])
        )
        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertIn("error", response_json)
        self.assertEqual(response_json["error"], gettext("File not found in upload session"))

    def test_delete_uploaded_file(self):
        """Delete an uploaded file."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UploadedFile.objects.filter(name="testfile.txt").exists())

    @patch("recordtransfer.views.settings.DEBUG", True)
    def test_get_uploaded_file_in_debug(self):
        response = self.client.get(self.url)
        self.assertEqual(response.url, self.uploaded_file.get_file_media_url())

    @patch("recordtransfer.views.settings.DEBUG", False)
    def test_get_uploaded_file_in_production(self):
        response = self.client.get(self.url)
        self.assertIn("X-Accel-Redirect", response.headers)
        self.assertEqual(
            response.headers["X-Accel-Redirect"], self.uploaded_file.get_file_media_url()
        )

    def tearDown(self):
        UploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()


@patch("recordtransfer.emails.send_user_account_updated.delay", lambda a, b: None)
class TestUserProfileView(TestCase):
    def setUp(self):
        self.test_username = "testuser"
        self.test_first_name = "Test"
        self.test_last_name = "User"
        self.test_email = "testuser@example.com"
        self.test_current_password = "old_password"
        self.test_gets_notification_emails = True
        self.test_new_password = "new_password123"
        self.user = User.objects.create_user(
            username=self.test_username,
            first_name=self.test_first_name,
            last_name=self.test_last_name,
            email=self.test_email,
            password=self.test_current_password,
            gets_notification_emails=self.test_gets_notification_emails,
        )
        self.client.login(username="testuser", password="old_password")
        self.url = reverse("recordtransfer:userprofile")
        self.error_message = "There was an error updating your preferences. Please try again."
        self.success_message = "Preferences updated"
        self.password_change_success_message = "Password updated"

    def test_access_authenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")

    def test_access_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_valid_name_change(self):
        form_data = {
            "first_name": "New",
            "last_name": "Name",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_accented_name_change(self):
        form_data = {
            "first_name": "Áccéntéd",
            "last_name": "Námé",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_invalid_first_name(self):
        form_data = {
            "first_name": "123",
            "last_name": self.test_last_name,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_invalid_last_name(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": "123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_valid_notification_setting_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": False,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_invalid_notification_setting_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": self.test_gets_notification_emails,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_valid_password_change(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Password updated")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new_password123"))

    def test_wrong_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": "wrong_password",
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_passwords_do_not_match(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "new_password": "new_password123",
            "confirm_new_password": "different_password",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_same_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "new_password": self.test_current_password,
            "confirm_new_password": self.test_current_password,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_missing_current_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "new_password": "new_password123",
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_missing_new_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "current_password": self.test_current_password,
            "confirm_new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_missing_confirm_new_password(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": True,
            "current_password": self.test_current_password,
            "new_password": "new_password123",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_no_changes(self):
        form_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "gets_notification_emails": self.test_gets_notification_emails,
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )

    def test_empty_form_submission(self):
        form_data = {}
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordtransfer/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            self.error_message,
        )
