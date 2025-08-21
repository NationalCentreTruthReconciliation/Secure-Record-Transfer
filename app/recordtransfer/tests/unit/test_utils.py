import unittest
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from recordtransfer.models import TempUploadedFile, UploadSession
from recordtransfer.utils import (
    MAGIC_AVAILABLE,
    accept_file,
    accept_session,
    count_file_types,
    get_human_readable_file_count,
    get_human_readable_size,
    get_js_translation_version,
    html_to_text,
    snake_to_camel_case,
)


class NullLogger:
    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    def debug(self, *args, **kwargs):
        return

    def info(self, *args, **kwargs):
        return

    def warning(self, *args, **kwargs):
        return

    def warn(self, *args, **kwargs):
        return

    def error(self, *args, **kwargs):
        return


class HtmlToTextTests(TestCase):
    def test_empty_string(self):
        text = html_to_text("")
        self.assertEqual(text, "")

    def test_simple_tag_removal(self):
        text = html_to_text("<h1>Hello</h1>")
        self.assertEqual(text, "Hello")

    def test_nested_tags(self):
        text = html_to_text("<div><div><p>Hello</p></div></div>")
        self.assertEqual(text, "Hello")

    def test_whitespace_stripped(self):
        html = "\n".join(
            [
                "",
                "<html>",
                "    <div> Hello  </div>",
                "    ",
                "</html>",
            ]
        )
        text = html_to_text(html)
        self.assertEqual(text, "Hello")


class SnakeToCamelCaseTests(TestCase):
    def test_empty_string(self):
        camel_case = snake_to_camel_case("")
        self.assertEqual(camel_case, "")

    def test_no_underscores(self):
        camel_case = snake_to_camel_case("encyclopedia")
        self.assertEqual(camel_case, "encyclopedia")

    def test_with_underscores(self):
        camel_case = snake_to_camel_case("very_important_material")
        self.assertEqual(camel_case, "veryImportantMaterial")


class HumanReadableSizeUtilityTests(TestCase):
    def test_raises_for_invalid_base(self):
        self.assertRaises(ValueError, get_human_readable_size, 12335415, base=10)

    def test_raises_for_negative_size(self):
        self.assertRaises(ValueError, get_human_readable_size, -81235283)

    def test_bytes_less_than_base(self):
        param_list = [
            (0, 1024, "0 B"),
            (0, 1000, "0 B"),
            (5, 1024, "5 B"),
            (5, 1000, "5 B"),
            (1023, 1024, "1023 B"),
            (999, 1000, "999 B"),
        ]
        for size_bytes, base, expected in param_list:
            with self.subTest():
                size = get_human_readable_size(size_bytes, base=base, precision=2)
                self.assertEqual(size, expected)

    def test_bytes_equal_to_base_power(self):
        param_list = [
            (1024, 1024, "1.00 KiB"),
            (1000, 1000, "1.00 KB"),
            (1024**2, 1024, "1.00 MiB"),
            (1000**2, 1000, "1.00 MB"),
            (1024**3, 1024, "1.00 GiB"),
            (1000**3, 1000, "1.00 GB"),
            (1024**4, 1024, "1.00 TiB"),
            (1000**4, 1000, "1.00 TB"),
        ]
        for size_bytes, base, expected in param_list:
            with self.subTest():
                size = get_human_readable_size(size_bytes, base=base, precision=2)
                self.assertEqual(size, expected)

    def test_in_between_sizes(self):
        param_list = [
            ((1024**2) / 2, 1024, "512.00 KiB"),
            ((1000**3) / 2, 1000, "500.00 MB"),
        ]
        for size_bytes, base, expected in param_list:
            with self.subTest():
                size = get_human_readable_size(size_bytes, base=base, precision=2)
                self.assertEqual(size, expected)


class FileCountingUtilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.accepted_formats = {
            "Microsoft Word Document": [
                "doc",
                "docx",
            ],
            "Microsoft Excel Spreadsheet": [
                "xls",
                "xlsx",
            ],
            "Image": [
                "jpg",
                "png",
            ],
            "Audio": [
                "acc",
                "mp3",
            ],
        }
        cls.null_logger = NullLogger()

    def test_no_files_counted(self):
        counted_types = count_file_types([], self.accepted_formats)
        self.assertEqual(counted_types, {})

    def test_no_accepted_file_types(self):
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf"], self.accepted_formats
        )
        self.assertEqual(counted_types, {})

    def test_one_file_counted(self):
        counted_types = count_file_types(["song1.mp3"], self.accepted_formats)
        self.assertEqual(counted_types, {"Audio": 1})

    def test_multiple_of_one_file_type_counted(self):
        counted_types = count_file_types(
            ["file1.doc", "file2.doc", "file3.docx"], self.accepted_formats
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 3})

    def test_multiple_different_files_counted(self):
        counted_types = count_file_types(
            ["file1.doc", "file2.doc", "song1.mp3", "song1.acc", "sheet1.xls", "sheet2.xlsx"],
            self.accepted_formats,
        )
        self.assertEqual(
            counted_types,
            {
                "Microsoft Word Document": 2,
                "Audio": 2,
                "Microsoft Excel Spreadsheet": 2,
            },
        )

    def test_uppercase_extensions_are_counted(self):
        counted_types = count_file_types(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"], self.accepted_formats
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 4})

    def test_unaccepted_files_ignored(self):
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf", "file4.docx"], self.accepted_formats
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 1})

    def test_no_files_human_readable(self):
        statement = get_human_readable_file_count([], self.accepted_formats)
        self.assertEqual(statement, "No file types could be identified")

    def test_no_accepted_file_types_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.pages", "file2.docs", "file3.pdf"], self.accepted_formats
        )
        self.assertEqual(statement, "No file types could be identified")

    def test_one_file_group_singular_human_readable(self):
        statement = get_human_readable_file_count(["file1.DOC"], self.accepted_formats)
        self.assertEqual(statement, "1 Microsoft Word Document file")

    def test_one_file_group_plural_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"], self.accepted_formats
        )
        self.assertEqual(statement, "4 Microsoft Word Document files")

    def test_two_groups_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "song1.mp3", "img1.jpg", "img2.png", "img3.png"],
            self.accepted_formats,
        )
        self.assertIn("2 Microsoft Word Document files", statement)
        self.assertIn("1 Audio file", statement)
        self.assertIn("3 Image files", statement)


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["pdf", "txt"], "Image": ["jpg", "png"]},
)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE_MB", 3)
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE_MB", 1)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
class TestAcceptFile(TestCase):
    """Tests for accept_file method."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test data."""
        super().setUpClass()

    @staticmethod
    def generate_uploaded_file(filename: str = "") -> UploadedFile:
        """Generate a UploadedFile instance with minimal content based on the file's extension."""
        content_map = {
            "pdf": b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n",  # PDF header
            "txt": b"This is a text file content",  # Plain text
            "jpg": (
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
                b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
                b"\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d"
                b"\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444"
                b"\x1f'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11"
                b"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08"
                b"\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01"
                b"\x00\x00?\x00\x00\xff\xd9"  # Minimal JPEG file
            ),
            "png": (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
                b"\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
                b"\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x1c\x00"
                b"\x00\x00\x00IEND\xaeB`\x82"  # Minimal PNG file
            ),
            # Malicious content types for testing
            "exe": b"MZ\x90\x00",  # Windows PE header
            "elf": (
                b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x02\x00>\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x40\x00\x38\x00\x01\x00\x00\x00\x00\x00\x00\x00"
            ),  # Extended Linux ELF header that gets detected as executable
            "script": b"#!/bin/bash\necho 'malicious'",  # Shell script
            "html": b"<!DOCTYPE html><html><body>",  # HTML content
        }
        return SimpleUploadedFile(
            filename,
            content_map.get(filename.split(".")[-1].lower(), b"test content"),
        )

    def test_accept_file_valid(self) -> None:
        """Test that valid files are accepted with matching MIME types."""
        param_list = [
            ("My File.pdf", 1),
            ("My File.PDF", 1),
            ("My File.PDf", 1),
            ("My.File.PDf", 1024),
            ("My File.txt", 991),
            ("My File.jpg", 9081),
            ("My File.png", 512),
        ]
        for filename, filesize in param_list:
            with self.subTest(filename=filename):
                result = accept_file(filename, filesize, self.generate_uploaded_file(filename))
                self.assertTrue(result["accepted"])

    @unittest.skipUnless(MAGIC_AVAILABLE, "libmagic is required for MIME type validation tests")
    def test_accept_file_mime_type_mismatch(self) -> None:
        """Test that files with mismatched MIME types are rejected."""
        # Test cases where file extension doesn't match actual content
        test_cases = [
            # Executable disguised as PDF
            ("malware.pdf", 1024, "malware.exe"),  # Windows PE header
            # Executable disguised as text file
            ("malware.txt", 1024, "malware.elf"),  # Linux ELF header
            # Script disguised as image file
            ("script.jpg", 1024, "script.sh"),  # Shell script
            # HTML file disguised as PDF
            ("fake.pdf", 1024, "fake.html"),  # HTML content
            # PNG content with JPG extension
            ("fake.jpg", 1024, "fake.png"),  # PNG content but .jpg extension
        ]

        for filename, filesize, content_filename in test_cases:
            with self.subTest(filename=filename):
                result = accept_file(
                    filename, filesize, self.generate_uploaded_file(content_filename)
                )
                print(result)
                # The file should be rejected due to MIME type mismatch
                self.assertFalse(result["accepted"])
                self.assertIn("MIME type mismatch", result.get("error", ""))

    def test_accept_file_invalid_extension(self) -> None:
        """Test that files with invalid extensions are rejected."""
        param_list = [
            "p",
            "mp3",
            "docx",  # Not in our accepted formats anymore
            "xlsx",  # Not in our accepted formats anymore
        ]
        for extension in param_list:
            with self.subTest():
                file_name = f"My File.{extension}"
                result = accept_file(file_name, 9012, self.generate_uploaded_file(file_name))
                self.assertFalse(result["accepted"])
                self.assertIn("extension", result["error"])

    def test_accept_file_missing_extension(self) -> None:
        """Test that files without an extension are rejected."""
        file = SimpleUploadedFile("No Extension File", b"test content")
        result = accept_file("No Extension File", 209, file)
        self.assertFalse(result["accepted"])
        self.assertIn("extension", result["error"])

    def test_malicious_file_names(self) -> None:
        """Test that malicious filenames are not accepted."""
        param_list = [
            "file\x00name.pdf",  # control character in file name
            "A" * 300 + ".pdf",  # buffer overflow attempt
            "/".join(["A" * 100] * 10) + "/malicious.pdf",  # very long path components
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fuser%2freport.pdf",  # URL encoded traversal
            "../../../user/document.txt",  # relative path
            "/opt/secure-record-transfer/users.jpg",  # absolute path
            "C:/Program Files (x86)/users.png",  # absolute Windows path
            "COM5.pdf",  # Windows reserved file name
        ]
        for filename in param_list:
            with self.subTest():
                result = accept_file(filename, 512, self.generate_uploaded_file(filename))
                self.assertFalse(result["accepted"])

    def test_invalid_size(self) -> None:
        """Test that files with invalid sizes are rejected."""
        param_list = [
            -1,
            -1000,
        ]
        for size in param_list:
            with self.subTest():
                file_name = "My File.pdf"
                result = accept_file(file_name, size, self.generate_uploaded_file(file_name))
                self.assertFalse(result["accepted"])
                self.assertIn("size is invalid", result["error"])

    def test_empty_file(self) -> None:
        """Test that empty files are rejected."""
        file = SimpleUploadedFile("empty.pdf", b"")
        result = accept_file("empty.pdf", 0, file)
        self.assertFalse(result["accepted"])
        self.assertIn("empty", result["error"])

    def test_file_too_large(self) -> None:
        """Test that files that are too large are rejected."""
        # Max size is patched to 1 MB
        param_list = [
            (1000**2) + 1,  # 1 MB plus one byte
            (1000**2) * 8,  # 8 MB
            (1000**2) * 32,  # 32 MB
            (1000**3),  # 1 GB
            (1000**4),  # 1 TB
        ]
        for size in param_list:
            with self.subTest():
                file_name = "My File.pdf"
                result = accept_file(file_name, size, self.generate_uploaded_file(file_name))
                self.assertFalse(result["accepted"])
                self.assertIn("File is too big", result["error"])

    def test_file_exactly_max_size(self) -> None:
        """Test that files that are exactly the max size are accepted."""
        # Max size is patched to 1 MB
        file_name = "My File.pdf"
        result = accept_file(
            file_name, ((1000**2) * 1), self.generate_uploaded_file(file_name)
        )  # 1 MB
        self.assertTrue(result["accepted"])


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE_MB", 3)
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE_MB", 1)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
class TestAcceptSession(TestCase):
    """Tests for accept_session method."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test data."""
        super().setUpClass()

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.session_1 = UploadSession.objects.create(
            token="test_session_1",
            started_at=timezone.now(),
        )
        cls.one_mb = bytearray([1] * (1000**2))
        cls.half_mb = bytearray([1] * int((1000**2) / 2))

    def tearDown(self) -> None:
        """Remove all uploaded files after each test."""
        TempUploadedFile.objects.all().delete()

    def test_session_has_room(self) -> None:
        """Test that a session with room for more files is accepted."""
        # 2 MB of files (one MB x 2)
        for name in ("File 1.docx", "File 2.docx"):
            TempUploadedFile.objects.create(
                session=self.session_1,
                file_upload=SimpleUploadedFile(name, self.one_mb),
                name=name,
            )
        self.session_1.status = UploadSession.SessionStatus.UPLOADING
        for size in ("1000", len(self.one_mb)):
            with self.subTest():
                result = accept_session("My File.pdf", size, self.session_1)
                self.assertTrue(result["accepted"])

    def test_session_file_count_full(self) -> None:
        """Test that a session with the maximum number of files is rejected."""
        # 2 MB of files (half MB x 4)
        # Max file count is 4
        for name in ("File 1.docx", "File 2.pdf", "File 3.pdf", "File 4.pdf"):
            TempUploadedFile.objects.create(
                session=self.session_1,
                name=name,
                file_upload=SimpleUploadedFile(name, self.half_mb),
            )
        self.session_1.status = UploadSession.SessionStatus.UPLOADING
        result = accept_session("My File.pdf", "1000", self.session_1)
        self.assertFalse(result["accepted"])
        self.assertIn("You can not upload anymore files", result["error"])

    def test_file_too_large_for_session(self) -> None:
        """Test that a file that is too large for the session is rejected."""
        # 2.5 MB of files (1 MB x 2, 0.5 MB x 1)
        for name, content in (
            ("File 1.docx", self.one_mb),
            ("File 2.pdf", self.one_mb),
            ("File 3.pdf", self.half_mb),
        ):
            TempUploadedFile.objects.create(
                session=self.session_1,
                name=name,
                file_upload=SimpleUploadedFile(name, content),
            )
        self.session_1.status = UploadSession.SessionStatus.UPLOADING
        result = accept_session("My File.pdf", len(self.one_mb), self.session_1)
        self.assertFalse(result["accepted"])
        self.assertIn("Maximum total upload size (3 MB) exceeded", result["error"])

    def test_duplicate_file_name(self) -> None:
        """Test that a file with the same name as an existing file is rejected."""
        names = ("File.1.docx", "File.2.pdf")
        for name in names:
            TempUploadedFile.objects.create(
                session=self.session_1,
                name=name,
                file_upload=SimpleUploadedFile(name, self.half_mb),
            )
        self.session_1.status = UploadSession.SessionStatus.UPLOADING
        for name in names:
            with self.subTest():
                result = accept_session(name, "1000", self.session_1)
                self.assertTrue(result["accepted"])


class TestGetJsTranslationVersion(TestCase):
    """Tests for get_js_translation_version."""

    @override_settings(LOCALE_PATHS=[])
    def test_no_locale_paths(self) -> None:
        """Test that a default value of '0' is returned if there are no paths."""
        version = get_js_translation_version()
        self.assertEqual("0", version)
