import logging
import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.forms import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext
from upload.handles import HANDLE_TTL_SECONDS, SESSION_KEY
from upload.models import TempUploadedFile, UploadSession
from upload.views import UPLOAD_HANDLE_HEADER


def _set_handle(
    client: Client,
    handle: str,
    upload_session: UploadSession,
    ts: float | None = None,
) -> None:
    """Inject a handle -> upload_session mapping into the test client's session."""
    session = client.session
    handles = session.get(SESSION_KEY, {})
    handles[handle] = {"sid": upload_session.pk, "ts": ts if ts is not None else time.time()}
    session[SESSION_KEY] = handles
    session.save()


def _del_handle(
    client: Client,
    handle: str,
) -> None:
    """Delete a handle previously set in _set_handle()."""
    session = client.session
    handles = session.get(SESSION_KEY, {})
    if handle in handles:
        del handles[handle]
    session[SESSION_KEY] = handles
    session.save()


@override_settings(
    FILE_UPLOAD_ENABLED=True,
)
class TestListFilesView(TestCase):
    """Tests for listing uploaded files view."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = get_user_model().objects.create_user(
            username="testuser1", password="1X<ISRUkw+tuK"
        )

    def setUp(self) -> None:
        """Set up test environment."""
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.session = UploadSession.new_session(self.test_user_1)
        self.handle = "deadbeef" * 4  # 32-char opaque handle for tests
        _set_handle(self.client, self.handle, self.session)

    def test_list_files_with_valid_handle(self) -> None:
        """List endpoint returns the session's files when handle is valid."""
        self.session.add_temp_file(SimpleUploadedFile("a.pdf", self.one_kib))
        response = self.client.get(
            reverse("upload:upload_files"),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["files"]), 1)

    def test_list_files_missing_handle(self) -> None:
        """Endpoint returns 400 if no handle is sent."""
        response = self.client.get(reverse("upload:upload_files"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertNotIn("uploadSessionToken", response.json())

    def test_list_files_unknown_handle(self) -> None:
        """Endpoint returns 400 if the handle is not registered."""
        response = self.client.get(
            reverse("upload:upload_files"),
            HTTP_X_UPLOAD_HANDLE="00000000" * 4,
        )
        self.assertEqual(response.status_code, 400)

    def test_list_other_users_files(self) -> None:
        """Test that a user cannot list another user's files."""
        self.client.logout()

        # Create a second user, log them in, register a handle in their session,
        # then attempt to use that same handle while logged in as user 1.
        other_user = get_user_model().objects.create_user(
            username="testuser2", password="1X<ISRUkw+tuK"
        )
        other_session = UploadSession.new_session(user=other_user)
        other_handle = "11112222" * 4
        self.client.login(username="testuser2", password="1X<ISRUkw+tuK")
        _set_handle(self.client, other_handle, other_session)
        self.client.logout()

        # Log back in as the original user, but now try to use testuser2's handle
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")

        response = self.client.get(
            reverse("upload:upload_files"),
            HTTP_X_UPLOAD_HANDLE=other_handle,
        )
        self.assertEqual(response.status_code, 400)

    def test_expired_handle_is_rejected(self) -> None:
        """Test that a handle with a timestamp older than the TTL is not resolvable."""
        stale_handle = "aaaabbbb" * 4
        _set_handle(
            self.client,
            stale_handle,
            self.session,
            ts=time.time() - (HANDLE_TTL_SECONDS + 5),
        )
        response = self.client.get(
            reverse("upload:upload_files"),
            HTTP_X_UPLOAD_HANDLE=stale_handle,
        )
        self.assertEqual(response.status_code, 400)

    def tearDown(self) -> None:
        """Tear down test environment."""
        TempUploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()
        self.client.logout()


@override_settings(
    ACCEPTED_FILE_FORMATS={"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
    FILE_UPLOAD_ENABLED=True,
    MAX_TOTAL_UPLOAD_SIZE_MB=3,
    MAX_SINGLE_UPLOAD_SIZE_MB=1,
    MAX_TOTAL_UPLOAD_COUNT=4,
)
class TestUploadFilesView(TestCase):
    """Test uploading files."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set logging level."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.one_kib = bytearray([1] * 1024)
        cls.test_user_1 = get_user_model().objects.create_user(
            username="testuser1", password="1X<ISRUkw+tuK"
        )

    def setUp(self) -> None:
        """Set up test environment."""
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.patch__accept_file = patch("upload.views.accept_file").start()
        self.patch__accept_session = patch("upload.views.accept_session").start()
        self.patch_check_for_malware = patch("upload.views.check_for_malware").start()
        self.patch__accept_file.return_value = {"accepted": True}
        self.patch__accept_session.return_value = {"accepted": True}

        self.session = UploadSession.new_session(user=self.test_user_1)
        self.handle = "deadbeef" * 4  # 32-char opaque handle for tests
        _set_handle(self.client, self.handle, self.session)

    def test_upload_file_with_valid_handle(self) -> None:
        """POST uploads a file when the handle is valid."""
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.pdf", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.session.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.file_count, 1)

    def test_cant_upload_if_not_logged_in(self) -> None:
        """Files should not be uploaded if the user is not logged in."""
        self.client.logout()
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.pdf", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.file_count, 0)

    def test_cant_upload_without_handle(self) -> None:
        """Test that an error is received if there is no session handle."""
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.pdf", self.one_kib)},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.session.file_count, 0)

    def test_cant_upload_with_invalid_handle(self) -> None:
        """Test that an error is received if there is no session handle."""
        _del_handle(self.client, self.handle)
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.pdf", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.session.file_count, 0)

    def test_500_error_caught(self) -> None:
        """Test that a 500 is returned if an error is raised."""
        self.patch__accept_file.side_effect = ValueError("err")
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())

    def test_no_files_uploaded(self) -> None:
        """Test that a 400 is returned if no files are uploaded."""
        response = self.client.post(
            reverse("upload:upload_files"),
            {},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 400)

    def test_cant_upload_with_other_user_handle(self) -> None:
        """Test that an error is received when a user tries to upload with another's token."""
        self.client.logout()

        # Start a new session as a different user
        other_user = get_user_model().objects.create_user(
            username="testuser2", password="1X<ISRUkw+tuK"
        )
        self.client.login(username="testuser2", password="1X<ISRUkw+tuK")

        # First try before making our own session for the new user
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        self.assertEqual(response.status_code, 400)

        # Try again after making our own session
        other_user_session = UploadSession.new_session(user=other_user)
        other_handle = "00001111" * 4
        _set_handle(self.client, other_handle, other_user_session)

        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(self.session.file_count, 0)

    def test_html_file_is_sanitized_after_malware_scan(self) -> None:
        """Test that HTML files are sanitized after malware scanning and before saving."""
        html_content = b'<html><body><script>alert("xss")</script><p>Safe</p></body></html>'

        def assert_unsanitized_during_malware_scan(file: UploadedFile) -> None:
            """Assert malware scanning sees the original file content."""
            file.seek(0)
            self.assertIn(b"<script>", file.read())
            file.seek(0)

        self.patch_check_for_malware.side_effect = assert_unsanitized_during_malware_scan
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.html", html_content, content_type="text/html")},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        self.session.refresh_from_db()  # type: ignore
        uploaded_file = self.session.get_file_by_name("File.html")
        uploaded_file.file_upload.open()
        saved_content = uploaded_file.file_upload.read()
        uploaded_file.file_upload.close()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"<script>", saved_content)
        self.assertNotIn(b"alert", saved_content)
        self.assertIn(b"<p>Safe</p>", saved_content)

    def test_file_issue_flagged(self) -> None:
        """Test that an issue is flagged if the file is not accepted."""
        self.patch__accept_file.return_value = {"accepted": False, "error": "ISSUE"}

        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        response_json = response.json()
        self.session.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "ISSUE")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(self.session.file_count, 0)

    def test_session_issue_flagged(self) -> None:
        """Test that an issue is flagged if the session is not accepted."""
        self.patch__accept_session.return_value = {"accepted": False, "error": "ISSUE"}

        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        response_json = response.json()
        self.session.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "ISSUE")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(self.session.file_count, 0)

    def test_malware_flagged(self) -> None:
        """Test that malware is flagged if the file contains malware."""
        self.patch_check_for_malware.side_effect = ValidationError("Malware found")
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        response_json = response.json()
        self.session.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json.get("error"), "Malware was detected in the file")
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(self.session.file_count, 0)

    def test_malware_scan_file_too_large(self) -> None:
        """Test that a ValueError from check_for_malware returns the correct error and status."""
        self.patch_check_for_malware.side_effect = ValueError(
            "File is too large to scan for malware"
        )
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        response_json = response.json()
        self.session.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response_json.get("error"), "The file was too large to be scanned for malware"
        )
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(self.session.file_count, 0)

    def test_malware_scan_connection_error(self) -> None:
        """Test that a ConnectionError from check_for_malware returns the correct error and
        status.
        """
        self.patch_check_for_malware.side_effect = ConnectionError(
            "Unable to scan file for malware due to scanner error"
        )
        response = self.client.post(
            reverse("upload:upload_files"),
            {"file": SimpleUploadedFile("File.PDF", self.one_kib)},
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )

        response_json = response.json()
        self.session.refresh_from_db()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response_json.get("error"),
            "There was an error while scanning the file. Please try again later.",
        )
        self.assertEqual(response_json.get("accepted"), False)
        self.assertEqual(self.session.file_count, 0)

    def tearDown(self) -> None:
        """Tear down test environment."""
        self.client.logout()

    @classmethod
    def tearDownClass(cls) -> None:
        """Tear down test class."""
        super().tearDownClass()
        logging.disable(logging.NOTSET)
        patch.stopall()


@override_settings(
    DEBUG=True,
    FILE_UPLOAD_ENABLED=True,
)
class TestGetUploadedFileByUUID(TestCase):
    """Test accessing files by UUID."""

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.one_kib = bytearray([1] * 1024)
        User = get_user_model()
        cls.test_user_1 = User.objects.create_user(
            username="testuser1",
            password="1X<ISRUkw+tuK",
        )
        cls.admin_user = User.objects.create_user(
            username="admin",
            password="3&SAjfTYZQ",
            is_staff=True,
        )

    def setUp(self) -> None:
        """Set up test environment."""
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.session = UploadSession.new_session(user=self.test_user_1)
        file_to_upload = SimpleUploadedFile("testfile.txt", self.one_kib)
        self.temp_file = self.session.add_temp_file(file_to_upload)

    def test_temp_file_access_ok(self) -> None:
        """Test a successful temp file access request."""
        response = self.client.get(
            reverse("upload:uploaded_file_by_uuid", args=[self.temp_file.uuid])
        )
        url = self.temp_file.get_file_media_url()
        self.assertEqual(response.url, url)

    @override_settings(DEBUG=False)
    def test_temp_file_access_prod_ok(self) -> None:
        """Test a successful temp file access request in production."""
        response = self.client.get(
            reverse("upload:uploaded_file_by_uuid", args=[self.temp_file.uuid])
        )
        self.assertEqual(response["X-Accel-Redirect"], self.temp_file.get_file_media_url())

    def test_perm_file_access_ok(self) -> None:
        """Test a succesful file access request for a perm file."""
        self.session.make_uploads_permanent()
        perm_file = self.session.permuploadedfile_set.first()
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_uuid",
                args=[perm_file.uuid],
            )
        )
        self.assertEqual(response.url, perm_file.get_file_media_url())

    @override_settings(DEBUG=False)
    def test_perm_file_access_prod_ok(self) -> None:
        """Test a succesful file access request for a perm file in production."""
        self.session.make_uploads_permanent()
        perm_file = self.session.permuploadedfile_set.first()
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_uuid",
                args=[perm_file.uuid],
            )
        )
        self.assertEqual(response["X-Accel-Redirect"], perm_file.get_file_media_url())

    def test_regular_user_cant_access_other_files(self) -> None:
        """Test that a regular non-staff user cannotget access another user's files."""
        self.client.logout()

        # Log in as a different user, and try to get the original user's file
        _ = get_user_model().objects.create_user(username="testuser2", password="8ASbruPeZma8$")

        self.client.login(username="testuser2", password="8ASbruPeZma8$")

        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_uuid",
                args=[self.temp_file.uuid],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_user_can_access_other_files(self) -> None:
        """Test that a staff user can access other users' files."""
        self.client.logout()

        self.client.login(username="admin", password="3&SAjfTYZQ")

        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_uuid",
                args=[self.temp_file.uuid],
            ),
        )
        self.assertEqual(response.url, self.temp_file.get_file_media_url())


@override_settings(
    DEBUG=True,
    FILE_UPLOAD_ENABLED=True,
)
class TestGetAndDeleteUploadedFileByName(TestCase):
    """Tests accessing and deleting files by name.

    This file access method works using upload session handles.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        super().setUpClass()
        logging.disable(logging.CRITICAL)

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.one_kib = bytearray([1] * 1024)
        User = get_user_model()
        cls.test_user_1 = User.objects.create_user(
            username="testuser1",
            password="1X<ISRUkw+tuK",
        )
        cls.admin_user = User.objects.create_user(
            username="admin",
            password="3&SAjfTYZQ",
        )

    def setUp(self) -> None:
        """Set up test environment."""
        _ = self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        self.session = UploadSession.new_session(user=self.test_user_1)

        self.handle = "deadbeef" * 4  # 32-char opaque handle for tests
        _set_handle(self.client, self.handle, self.session)

        self.temp_file = self.session.add_temp_file(
            SimpleUploadedFile("testfile.txt", self.one_kib)
        )

    def test_get_invalid_handle(self) -> None:
        """Test that getting from a non-existent session handle returns a 404.

        This can happen if a session handle expires, for example.
        """
        _del_handle(self.client, self.handle)
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_invalid_handle(self) -> None:
        """Test that deleting from a non-existent session handle returns a 404."""
        _del_handle(self.client, self.handle)
        response = self.client.delete(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 404)

    def test_get_file_not_found(self) -> None:
        """Test that getting a non-existent file returns a 404."""
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_name",
                args=["invalid_file.mp3"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_file_not_found(self) -> None:
        """Test that deleting a non-existent file returns a 404."""
        response = self.client.delete(
            reverse(
                "upload:uploaded_file_by_name",
                args=["invalid_file.mp3"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 404)

    def test_cant_get_other_users_file(self) -> None:
        """Test that a user cannot access another user's files."""
        self.client.logout()

        # Log in as a different user, and upload a different file
        other_user = get_user_model().objects.create_user(
            username="testuser2", password="8ASbruPeZma8$"
        )
        self.client.login(username="testuser2", password="8ASbruPeZma8$")
        other_session = UploadSession.new_session(other_user)
        other_handle = "abababab" * 4
        _set_handle(self.client, other_handle, other_session)
        other_session.add_temp_file(SimpleUploadedFile("otheruserfile.pdf", self.one_kib))
        self.client.logout()

        # Log back in as the original user, try to access the other file
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_name",
                args=["otheruserfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=other_handle,
        )
        self.assertEqual(response.status_code, 404)

    def test_cant_delete_other_users_file(self) -> None:
        """Test that a user cannot delete another user's files."""
        self.client.logout()

        # Log in as a different user, and upload a different file
        other_user = get_user_model().objects.create_user(
            username="testuser2", password="8ASbruPeZma8$"
        )
        self.client.login(username="testuser2", password="8ASbruPeZma8$")
        other_session = UploadSession.new_session(other_user)
        other_handle = "abababab" * 4
        _set_handle(self.client, other_handle, other_session)
        other_session.add_temp_file(SimpleUploadedFile("otheruserfile.pdf", self.one_kib))
        self.client.logout()

        # Log back in as the original user, try to delete the other file
        self.client.login(username="testuser1", password="1X<ISRUkw+tuK")
        response = self.client.delete(
            reverse(
                "upload:uploaded_file_by_name",
                args=["otheruserfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=other_handle,
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=True)
    def test_get_temp_file_ok(self) -> None:
        """Test getting the file in DEBUG mode."""
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.url, self.temp_file.get_file_media_url())

    @override_settings(DEBUG=False)
    def test_get_temp_file_ok_in_prod(self) -> None:
        """Test getting the file in production mode."""
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertIn("X-Accel-Redirect", response)
        self.assertEqual(response["X-Accel-Redirect"], self.temp_file.get_file_media_url())

    @override_settings(DEBUG=True)
    def test_delete_temp_file_ok(self) -> None:
        """Test that temp files can be deleted while uploading files."""
        response = self.client.delete(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 204)

    @override_settings(DEBUG=False)
    def test_delete_temp_file_ok_in_prod(self) -> None:
        """Test getting the file in production mode."""
        response = self.client.delete(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 204)

    def test_admin_cannot_tamper_with_files(self) -> None:
        """Test that the admins cannot GET or DELETE uploaded files other users are uploading."""
        # Login as admin
        self.client.logout()
        self.client.login(username="admin", password="3&SAjfTYZQ")

        # Try to delete it
        response = self.client.delete(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 404)

        # Try to get it
        response = self.client.get(
            reverse(
                "upload:uploaded_file_by_name",
                args=["testfile.txt"],
            ),
            HTTP_X_UPLOAD_HANDLE=self.handle,
        )
        self.assertEqual(response.status_code, 404)

    def tearDown(self) -> None:
        """Tear down test environment."""
        TempUploadedFile.objects.all().delete()
        UploadSession.objects.all().delete()
