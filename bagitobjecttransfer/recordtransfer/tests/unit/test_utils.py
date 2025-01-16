from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from recordtransfer.models import UploadedFile, UploadSession
from recordtransfer.utils import (
    accept_file,
    accept_session,
    count_file_types,
    get_human_readable_file_count,
    get_human_readable_size,
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
        counted_types = count_file_types([], self.accepted_formats, logger=self.null_logger)
        self.assertEqual(counted_types, {})

    def test_no_accepted_file_types(self):
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertEqual(counted_types, {})

    def test_one_file_counted(self):
        counted_types = count_file_types(
            ["song1.mp3"], self.accepted_formats, logger=self.null_logger
        )
        self.assertEqual(counted_types, {"Audio": 1})

    def test_multiple_of_one_file_type_counted(self):
        counted_types = count_file_types(
            ["file1.doc", "file2.doc", "file3.docx"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 3})

    def test_multiple_different_files_counted(self):
        counted_types = count_file_types(
            ["file1.doc", "file2.doc", "song1.mp3", "song1.acc", "sheet1.xls", "sheet2.xlsx"],
            self.accepted_formats,
            logger=self.null_logger,
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
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 4})

    def test_unaccepted_files_ignored(self):
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf", "file4.docx"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 1})

    def test_no_files_human_readable(self):
        statement = get_human_readable_file_count(
            [], self.accepted_formats, logger=self.null_logger
        )
        self.assertEqual(statement, "No file types could be identified")

    def test_no_accepted_file_types_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.pages", "file2.docs", "file3.pdf"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertEqual(statement, "No file types could be identified")

    def test_one_file_group_singular_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.DOC"], self.accepted_formats, logger=self.null_logger
        )
        self.assertEqual(statement, "1 Microsoft Word Document file")

    def test_one_file_group_plural_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertEqual(statement, "4 Microsoft Word Document files")

    def test_two_groups_human_readable(self):
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "song1.mp3", "img1.jpg", "img2.png", "img3.png"],
            self.accepted_formats,
            logger=self.null_logger,
        )
        self.assertIn("2 Microsoft Word Document files", statement)
        self.assertIn("1 Audio file", statement)
        self.assertIn("3 Image files", statement)


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE", 3)  # MiB
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE", 1)  # MiB
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_COUNT", 4)  # Number of files
class TestAcceptFile(TestCase):
    """Tests for accept_file method."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test data."""
        super().setUpClass()

    def test_accept_file_valid(self) -> None:
        """Test that valid files are accepted."""
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
                result = accept_file(filename, filesize)
                self.assertTrue(result["accepted"])

    def test_accept_file_invalid_extension(self) -> None:
        """Test that files with invalid extensions are rejected."""
        param_list = [
            "p",
            "mp3",
            "docxx",
        ]
        for extension in param_list:
            with self.subTest():
                result = accept_file(f"My File.{extension}", "9012")
                self.assertFalse(result["accepted"])
                self.assertIn("extension", result["error"])

    def test_accept_file_missing_extension(self) -> None:
        """Test that files without an extension are rejected."""
        result = accept_file("My File", "209")
        self.assertFalse(result["accepted"])
        self.assertIn("extension", result["error"])

    def test_invalid_size(self) -> None:
        """Test that files with invalid sizes are rejected."""
        param_list = [
            "-1",
            "-1000",
            "One thousand",
        ]
        for size in param_list:
            with self.subTest():
                result = accept_file("My File.pdf", size)
                self.assertFalse(result["accepted"])
                self.assertIn("size is invalid", result["error"])

    def test_empty_file(self) -> None:
        """Test that empty files are rejected."""
        result = accept_file("My File.pdf", "0")
        self.assertFalse(result["accepted"])
        self.assertIn("empty", result["error"])

    def test_file_too_large(self) -> None:
        """Test that files that are too large are rejected."""
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
                result = accept_file("My File.pdf", size)
                self.assertFalse(result["accepted"])
                self.assertIn("File is too big", result["error"])

    def test_file_exactly_max_size(self) -> None:
        """Test that files that are exactly the max size are accepted."""
        # Max size is patched to 1 MiB
        result = accept_file("My File.pdf", ((1024**2) * 1))  # 1 MiB
        self.assertTrue(result["accepted"])


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {"Document": ["docx", "pdf"], "Spreadsheet": ["xlsx"]},
)
@patch("django.conf.settings.MAX_TOTAL_UPLOAD_SIZE", 3)  # MiB
@patch("django.conf.settings.MAX_SINGLE_UPLOAD_SIZE", 1)  # MiB
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
        cls.one_mib = bytearray([1] * (1024**2))
        cls.half_mib = bytearray([1] * int((1024**2) / 2))

    def tearDown(self) -> None:
        """Remove all uploaded files after each test."""
        UploadedFile.objects.all().delete()

    def test_session_has_room(self) -> None:
        """Test that a session with room for more files is accepted."""
        # 2 MiB of files (one MiB x 2)
        for name in ("File 1.docx", "File 2.docx"):
            UploadedFile.objects.create(
                session=self.session_1,
                file_upload=SimpleUploadedFile(name, self.one_mib),
                name=name,
            )
        for size in ("1024", len(self.one_mib)):
            with self.subTest():
                result = accept_session("My File.pdf", size, self.session_1)
                self.assertTrue(result["accepted"])

    def test_session_file_count_full(self) -> None:
        """Test that a session with the maximum number of files is rejected."""
        # 2 MiB of files (half MiB x 4)
        # Max file count is 4
        for name in ("File 1.docx", "File 2.pdf", "File 3.pdf", "File 4.pdf"):
            UploadedFile.objects.create(
                session=self.session_1,
                name=name,
                file_upload=SimpleUploadedFile(name, self.half_mib),
            )
        result = accept_session("My File.pdf", "1024", self.session_1)
        self.assertFalse(result["accepted"])
        self.assertIn("You can not upload anymore files", result["error"])

    def test_file_too_large_for_session(self) -> None:
        """Test that a file that is too large for the session is rejected."""
        # 2.5 MiB of files (1 Mib x 2, 0.5 MiB x 1)
        for name, content in (
            ("File 1.docx", self.one_mib),
            ("File 2.pdf", self.one_mib),
            ("File 3.pdf", self.half_mib),
        ):
            UploadedFile.objects.create(
                session=self.session_1,
                name=name,
                file_upload=SimpleUploadedFile(name, content),
            )
        result = accept_session("My File.pdf", len(self.one_mib), self.session_1)
        self.assertFalse(result["accepted"])
        self.assertIn("Maximum total upload size (3 MiB) exceeded", result["error"])

    def test_duplicate_file_name(self) -> None:
        """Test that a file with the same name as an existing file is rejected."""
        names = ("File.1.docx", "File.2.pdf")
        for name in names:
            UploadedFile.objects.create(
                session=self.session_1,
                name=name,
                file_upload=SimpleUploadedFile(name, self.half_mib),
            )
        for name in names:
            with self.subTest():
                result = accept_session(name, "1024", self.session_1)
                self.assertFalse(result["accepted"])
                self.assertIn(
                    "A file with the same name has already been uploaded",
                    result["error"],
                )
