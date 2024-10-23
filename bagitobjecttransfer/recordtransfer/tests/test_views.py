import logging
from unittest import skipIf
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
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
    "recordtransfer.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("recordtransfer.settings.MAX_TOTAL_UPLOAD_SIZE", 3)  # MiB
@patch("recordtransfer.settings.MAX_SINGLE_UPLOAD_SIZE", 1)  # MiB
@patch("recordtransfer.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
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
        self.patch__accept_file = patch("recordtransfer.views._accept_file").start()
        self.patch__accept_session = patch("recordtransfer.views._accept_session").start()
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
            HTTP_Upload_Session_Token=session.token,
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
        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_json["issues"]), 1)
        self.assertEqual(response_json["issues"][0]["error"], "ISSUE")
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
        session = UploadSession.objects.filter(token=response_json["uploadSessionToken"]).first()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_json["issues"]), 1)
        self.assertEqual(response_json["issues"][0]["error"], "ISSUE")
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


@patch(
    "recordtransfer.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("recordtransfer.settings.MAX_TOTAL_UPLOAD_SIZE", 3)  # MiB
@patch("recordtransfer.settings.MAX_SINGLE_UPLOAD_SIZE", 1)  # MiB
@patch("recordtransfer.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
@override_storage(storage=LocMemStorage())
class TestAcceptFileView(TestCase):
    """Tests for recordtransfer:checkfile view"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls):
        cls.session_1 = UploadSession.objects.create(
            token="test_session_1",
            started_at=timezone.now(),
        )
        cls.one_mib = bytearray([1] * (1024**2))
        cls.half_mib = bytearray([1] * int((1024**2) / 2))
        cls.test_user_1 = User.objects.create_user(username="testuser1", password="1X<ISRUkw+tuK")

    def setUp(self):
        # Log in
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")

    def test_logged_out_error(self):
        self.client.logout()
        response = self.client.get(
            reverse("recordtransfer:checkfile"), {"filesize": "190", "filename": "My File.pdf"}
        )
        self.assertEqual(response.status_code, 302)

    def test_filename_missing(self):
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filesize": "190",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_file_name_empty(self):
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "",
                "filesize": "6123",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_filesize_missing(self):
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "My File.pdf",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_filesize_empty(self):
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "My File.pdf",
                "filesize": "",
            },
        )
        self.assertEqual(response.status_code, 400)

    @patch("recordtransfer.views._accept_file")
    def test_500_error_caught(self, patch__accept_file):
        patch__accept_file.side_effect = ValueError("err")
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "My File.pdf",
                "filesize": "1024",
            },
        )
        self.assertEqual(response.status_code, 500)

    def test_filename_filesize_ok(self):
        param_list = [
            ("My File.pdf", "1"),
            ("My File.PDF", "1"),
            ("My File.PDf", "1"),
            ("My.File.PDf", "1024"),
            ("My File.docx", "991"),
            ("My File.xlsx", "9081"),
        ]
        for filename, filesize in param_list:
            with self.subTest():
                response = self.client.get(
                    reverse("recordtransfer:checkfile"),
                    {
                        "filename": filename,
                        "filesize": filesize,
                    },
                )
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertTrue(response_json["accepted"], True)

    def test_file_extension_not_okay(self):
        param_list = [
            "p",
            "mp3",
            "docxx",
        ]
        for extension in param_list:
            with self.subTest():
                response = self.client.get(
                    reverse("recordtransfer:checkfile"),
                    {
                        "filename": f"My File.{extension}",
                        "filesize": "9012",
                    },
                )
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertFalse(response_json["accepted"])
                self.assertIn("extension", response_json["error"])

    def test_file_extension_missing(self):
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "My File",
                "filesize": "209",
            },
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertFalse(response_json["accepted"])
        self.assertIn("extension", response_json["error"])

    def test_invalid_size(self):
        param_list = [
            "-1",
            "-1000",
            "One thousand",
        ]
        for size in param_list:
            with self.subTest():
                response = self.client.get(
                    reverse("recordtransfer:checkfile"),
                    {
                        "filename": "My File.pdf",
                        "filesize": size,
                    },
                )
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertFalse(response_json["accepted"])
                self.assertIn("size is invalid", response_json["error"])

    def test_empty_file(self):
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "My File.pdf",
                "filesize": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertFalse(response_json["accepted"])
        self.assertIn("empty", response_json["error"])

    def test_file_too_large(self):
        # Max size is patched to 1 MiB
        param_list = [
            (1024**2) + 1,  # 1 MiB plus one byte
            (1024**2) * 8,  # 8 MiB
            (1024**2) * 32,  # 32 MiB
            (1024**3),  # 1 GiB
            (1024**4),  # 1 TiB
        ]
        for size in param_list:
            with self.subTest():
                response = self.client.get(
                    reverse("recordtransfer:checkfile"),
                    {
                        "filename": "My File.pdf",
                        "filesize": size,
                    },
                )
                self.assertEqual(response.status_code, 200)
                response_json = response.json()
                self.assertFalse(response_json["accepted"])
                self.assertIn("File is too big", response_json["error"])

    def test_file_exactly_max_size(self):
        # Max size is patched to 1 MiB
        response = self.client.get(
            reverse("recordtransfer:checkfile"),
            {
                "filename": "My File.pdf",
                "filesize": ((1024**2) * 1),  # 1 MiB
            },
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertTrue(response_json["accepted"])

    def test_session_has_room(self):
        files = []
        try:
            # 2 MiB of files (one MiB x 2)
            files = [
                UploadedFile.objects.create(
                    session=self.session_1,
                    file_upload=SimpleUploadedFile(name, self.one_mib),
                    name=name,
                )
                for name in ("File 1.docx", "File 2.docx")
            ]

            for size in ("1024", len(self.one_mib)):
                with self.subTest():
                    response = self.client.post(
                        reverse("recordtransfer:checkfile"),
                        {
                            "filename": "My File.pdf",
                            "filesize": size,
                        },
                        HTTP_Upload_Session_Token="test_session_1",
                    )
                    self.assertEqual(response.status_code, 200)
                    response_json = response.json()
                    self.assertTrue(response_json["accepted"])

        finally:
            for file_ in files:
                file_.delete()

    def test_session_file_count_full(self):
        files = []
        try:
            # 2 MiB of files (half MiB x 4)
            # Max file count is 4
            files = [
                UploadedFile.objects.create(
                    session=self.session_1,
                    name=name,
                    file_upload=SimpleUploadedFile(name, self.half_mib),
                )
                for name in ("File 1.docx", "File 2.pdf", "File 3.pdf", "File 4.pdf")
            ]

            response = self.client.post(
                reverse("recordtransfer:checkfile"),
                {
                    "filename": "My File.pdf",
                    "filesize": "1024",
                },
                HTTP_Upload_Session_Token="test_session_1",
            )

            self.assertEqual(response.status_code, 200)
            response_json = response.json()
            self.assertFalse(response_json["accepted"])
            self.assertIn("You can not upload anymore files", response_json["error"])

        finally:
            for file_ in files:
                file_.delete()

    def test_file_too_large_for_session(self):
        files = []
        try:
            # 2.5 MiB of files (1 Mib x 2, 0.5 MiB x 1)
            files = [
                UploadedFile.objects.create(
                    session=self.session_1,
                    name=name,
                    file_upload=SimpleUploadedFile(name, content),
                )
                for name, content in (
                    ("File 1.docx", self.one_mib),
                    ("File 2.pdf", self.one_mib),
                    ("File 3.pdf", self.half_mib),
                )
            ]

            response = self.client.post(
                reverse("recordtransfer:checkfile"),
                {
                    "filename": "My File.pdf",
                    "filesize": len(self.one_mib),
                },
                HTTP_Upload_Session_Token="test_session_1",
            )

            self.assertEqual(response.status_code, 200)
            response_json = response.json()
            self.assertFalse(response_json["accepted"])
            self.assertIn("Maximum total upload size (3 MiB) exceeded", response_json["error"])

        finally:
            for file_ in files:
                file_.delete()

    def test_duplicate_file_name(self):
        files = []
        names = ("File.1.docx", "File.2.pdf")
        try:
            files = [
                UploadedFile.objects.create(
                    session=self.session_1,
                    name=name,
                    file_upload=SimpleUploadedFile(name, self.half_mib),
                )
                for name in names
            ]

            for name in names:
                with self.subTest():
                    response = self.client.post(
                        reverse("recordtransfer:checkfile"),
                        {
                            "filename": name,
                            "filesize": "1024",
                        },
                        HTTP_Upload_Session_Token="test_session_1",
                    )

                    self.assertEqual(response.status_code, 200)
                    response_json = response.json()
                    self.assertFalse(response_json["accepted"])
                    self.assertIn(
                        "A file with the same name has already been uploaded",
                        response_json["error"],
                    )

        finally:
            for file_ in files:
                file_.delete()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        logging.disable(logging.NOTSET)
        UploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()


@patch("recordtransfer.emails.send_user_account_updated.delay", lambda a, b: None)
class TestUserProfileView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="old_password",
            gets_notification_emails=True,
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

    def test_valid_notification_setting_change(self):
        form_data = {
            "gets_notification_emails": False,
            "current_password": "",
            "new_password": "",
            "confirm_new_password": "",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), self.success_message)

    def test_invalid_notification_setting_change(self):
        form_data = {
            "gets_notification_emails": True,
            "current_password": "",
            "new_password": "",
            "confirm_new_password": "",
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
            "gets_notification_emails": True,
            "current_password": "old_password",
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
            "gets_notification_emails": True,
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
            "gets_notification_emails": True,
            "current_password": "old_password",
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
            "gets_notification_emails": True,
            "current_password": "old_password",
            "new_password": "old_password",
            "confirm_new_password": "old_password",
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
            "gets_notification_emails": True,
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
            "gets_notification_emails": True,
            "current_password": "old_password",
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
            "gets_notification_emails": True,
            "current_password": "old_password",
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
            "gets_notification_emails": True,
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
