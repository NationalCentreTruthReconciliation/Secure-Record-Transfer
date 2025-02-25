import logging
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext

from recordtransfer.enums import TransferStep
from recordtransfer.models import TempUploadedFile, UploadSession, User


class TestCreateUploadSessionView(TestCase):
    """Tests for recordtransfer:create_upload_session view."""

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Create user accounts."""
        cls.test_user = User.objects.create_user(username="testuser", password="1X<ISRUkw+tuK")

    def setUp(self) -> None:
        """Set up test environment."""
        self.client.login(username="testuser", password="1X<ISRUkw+tuK")
        self.url = reverse("recordtransfer:create_upload_session")

        # Set up client session data
        session = self.client.session
        session["wizard_transfer_form_wizard"] = {"step": TransferStep.UPLOAD_FILES.value}
        session.save()

    def tearDown(self) -> None:
        """Tear down test environment."""
        self.client.logout()

    def test_create_upload_session_success(self) -> None:
        """Test successful creation of an upload session."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()
        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(
            UploadSession.objects.filter(token=response_json["uploadSessionToken"]).exists()
        )

    def test_create_upload_session_logged_out(self) -> None:
        """Test that a 302 is returned if the user is not logged in."""
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    @patch("recordtransfer.views.media.UploadSession.new_session")
    def test_create_upload_session_error(self, mock_new_session: MagicMock) -> None:
        """Test that a 500 is returned if an error is raised."""
        mock_new_session.side_effect = Exception("Error creating session")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 500)
        response_json = response.json()
        self.assertIn("error", response_json)


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE_MB", 3)
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE_MB", 1)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
class TestUploadFilesView(TestCase):
    """Tests for recordtransfer:upload_files view."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set logging level."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = User.objects.create_user(username="testuser1", password="1X<ISRUkw+tuK")

    def setUp(self) -> None:
        """Set up test environment."""
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.patch__accept_file = patch("recordtransfer.views.media.accept_file").start()
        self.patch__accept_session = patch("recordtransfer.views.media.accept_session").start()
        self.patch_check_for_malware = patch(
            "recordtransfer.views.media.check_for_malware"
        ).start()
        self.patch__accept_file.return_value = {"accepted": True}
        self.patch__accept_session.return_value = {"accepted": True}

        # Set up client session data
        session = self.client.session
        session["wizard_transfer_form_wizard"] = {"step": TransferStep.UPLOAD_FILES.value}
        session.save()

        # Create a new upload session token
        self.session = UploadSession.new_session(user=self.test_user_1)
        self.token = self.session.token
        self.url = reverse("recordtransfer:upload_files", args=[self.token])

    def tearDown(self) -> None:
        """Tear down test environment."""
        TempUploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()
        self.client.logout()

    @classmethod
    def tearDownClass(cls) -> None:
        """Tear down test class."""
        super().tearDownClass()
        logging.disable(logging.NOTSET)
        patch.stopall()

    ## --- GET Request Tests --- ##
    def test_list_uploaded_files_invalid_session_token(self) -> None:
        """Invalid session token."""
        response = self.client.get(reverse("recordtransfer:upload_files", args=["invalid_token"]))
        self.assertEqual(response.status_code, 400)
        response_json = response.json()
        self.assertIn("error", response_json)

    def test_list_uploaded_files_invalid_user(self) -> None:
        """Invalid user for the session."""
        # Create a new session with a different user
        other_session = UploadSession.new_session(
            user=User.objects.create_user(username="testuser2", password="1X<ISRUkw+tuK")
        )
        # Try to access other user's session's files
        response = self.client.get(
            reverse("recordtransfer:upload_files", args=[other_session.token])
        )
        self.assertEqual(response.status_code, 400)
        response_json = response.json()
        self.assertIn("error", response_json)

    def test_list_uploaded_files_empty_session(self) -> None:
        """Session has no files."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json.get("files"), [])

    def test_list_uploaded_files_with_files(self) -> None:
        """Session has one file."""
        file_to_upload = SimpleUploadedFile("testfile.txt", self.one_kib)
        temp_file = self.session.add_temp_file(file_to_upload)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        response_files = response_json.get("files")
        self.assertEqual(len(response_files), 1)
        self.assertEqual(response_files[0]["name"], "testfile.txt")
        self.assertEqual(response_files[0]["size"], file_to_upload.size)
        self.assertEqual(response_files[0]["url"], temp_file.get_file_access_url())

    ## --- POST Request Tests --- ##

    def test_logged_out_error(self):
        """Test that a 302 is returned if the user is not logged in."""
        self.client.logout()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 302)

    def test_500_error_caught(self) -> None:
        """Test that a 500 is returned if an error is raised."""
        self.patch__accept_file.side_effect = ValueError("err")
        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )
        self.assertEqual(response.status_code, 500)

    def test_no_files_uploaded(self) -> None:
        """Test that a 400 is returned if no files are uploaded."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_same_session_used(self) -> None:
        """Test that the same session is used if the token is provided."""
        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("File.pdf", self.one_kib)},
        )

        self.session.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["uploadSessionToken"], self.token)
        self.assertEqual(self.session.file_count, 1)
        # Check that no error is raised if the uploaded file is looked up within the session
        self.session.get_temp_file_by_name("File.pdf")

    def test_error_from_invalid_token(self) -> None:
        """Test that a 400 error is received if the token is invalid."""
        response = self.client.post(
            reverse("recordtransfer:upload_files", args=["invalid_token"]),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.session.file_count, 0)

    def test_new_session_made_token_mismatch_user(self) -> None:
        """Test that a 400 error is received if the token does not match the user."""
        other_user = User.objects.create_user(username="testuser2", password="1X<ISRUkw+tuK")
        other_user_session = UploadSession.new_session(user=other_user)

        response = self.client.post(
            reverse("recordtransfer:upload_files", args=[other_user_session.token]),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )
        other_user_session.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(other_user_session.file_count, 0)

    def test_file_issue_flagged(self) -> None:
        """Test that an issue is flagged if the file is not accepted."""
        self.patch__accept_file.return_value = {"accepted": False, "error": "ISSUE"}

        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        response_json = response.json()

        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(response_json["uploadSessionToken"])

        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "ISSUE")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(session.file_count, 0)

    def test_session_issue_flagged(self) -> None:
        """Test that an issue is flagged if the session is not accepted."""
        self.patch__accept_session.return_value = {"accepted": False, "error": "ISSUE"}

        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        response_json = response.json()

        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(response_json["uploadSessionToken"])

        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "ISSUE")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(session.file_count, 0)

    def test_malware_flagged(self) -> None:
        """Test that malware is flagged if the file contains malware."""
        self.patch_check_for_malware.side_effect = ValidationError("Malware found")
        response = self.client.post(
            self.url,
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
        )

        response_json = response.json()

        self.assertIn("uploadSessionToken", response_json)
        self.assertTrue(response_json["uploadSessionToken"])

        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), 'Malware was detected in the file "File.PDF"')
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(session.file_count, 0)


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


class TestUploadedFileView(TestCase):
    """Tests for recordtransfer:uploaded_file view."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set logging level."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = User.objects.create_user(username="testuser1", password="1X<ISRUkw+tuK")

    def setUp(self) -> None:
        """Set up test environment."""
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.session = UploadSession.new_session(user=self.test_user_1)

        # Set up client session data
        session = self.client.session
        session["wizard_transfer_form_wizard"] = {"step": TransferStep.UPLOAD_FILES.value}
        session.save()

        file_to_upload = SimpleUploadedFile("testfile.txt", self.one_kib)
        self.temp_file = self.session.add_temp_file(
            SimpleUploadedFile("testfile.txt", self.one_kib)
        )
        self.url = reverse(
            "recordtransfer:uploaded_file", args=[self.session.token, file_to_upload.name]
        )

    def test_uploaded_file_session_not_found(self) -> None:
        """Invalid session token."""
        response = self.client.get(
            reverse("recordtransfer:uploaded_file", args=["invalid_token", "testfile.txt"])
        )
        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertIn("error", response_json)
        self.assertEqual(
            response_json["error"], gettext("Invalid filename or upload session token")
        )

    def test_uploaded_file_not_found(self) -> None:
        """Invalid file name in a valid session."""
        response = self.client.get(
            reverse("recordtransfer:uploaded_file", args=[self.session.token, "invalid_file.txt"])
        )
        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertIn("error", response_json)
        self.assertEqual(response_json["error"], gettext("File not found in upload session"))

    def test_uploaded_file_invalid_user(self) -> None:
        """Invalid user for the session."""
        self.session.user = User.objects.create_user(
            username="testuser2", password="1X<ISRUkw+tuK"
        )
        self.session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        response_json = response.json()
        self.assertIn("error", response_json)
        self.assertEqual(
            response_json["error"], gettext("Invalid filename or upload session token")
        )

    def test_delete_uploaded_file(self) -> None:
        """Delete an uploaded file."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(TempUploadedFile.objects.filter(name="testfile.txt").exists())

    def test_delete_uploaded_file_invalid_user(self) -> None:
        """Test delete with an invalid user for the session."""
        self.session.user = User.objects.create_user(
            username="testuser2", password="1X<ISRUkw+tuK"
        )
        self.session.save()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(TempUploadedFile.objects.filter(name="testfile.txt").exists())
        response_json = response.json()
        self.assertIn("error", response_json)
        self.assertEqual(
            response_json["error"], gettext("Invalid filename or upload session token")
        )

    @patch("recordtransfer.views.media.settings.DEBUG", True)
    def test_get_uploaded_file_in_debug(self) -> None:
        """Test getting the file in DEBUG mode."""
        response = self.client.get(self.url)
        self.assertEqual(response.url, self.temp_file.get_file_media_url())

    @patch("recordtransfer.views.media.settings.DEBUG", False)
    def test_get_uploaded_file_in_production(self) -> None:
        """Test getting the file in production mode."""
        response = self.client.get(self.url)
        self.assertIn("X-Accel-Redirect", response.headers)
        self.assertEqual(response.headers["X-Accel-Redirect"], self.temp_file.get_file_media_url())

    def tearDown(self) -> None:
        """Tear down test environment."""
        TempUploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()
