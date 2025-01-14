from unittest.mock import patch

from django.test import TestCase

from recordtransfer.utils import (
    count_file_types,
    get_human_readable_file_count,
    get_human_readable_size,
    html_to_text,
    snake_to_camel_case,
)


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
            (1.0, 1024, "1 B"),
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


@patch(
    "django.conf.settings.ACCEPTED_FILE_FORMATS",
    {
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
    },
)
class FileCountingUtilityTests(TestCase):
    """Tests for counting files of accepted file types."""

    def test_no_files_counted(self) -> None:
        """Test empty file list."""
        counted_types = count_file_types([])
        self.assertEqual(counted_types, {})

    def test_no_accepted_file_types(self) -> None:
        """Test when no files are of an accepted file type."""
        counted_types = count_file_types(["file1.pages", "file2.docs", "file3.pdf"])
        self.assertEqual(counted_types, {None: 3})

    def test_one_file_counted(self) -> None:
        """Test when only one file is of an accepted file type."""
        counted_types = count_file_types(["song1.mp3"])
        self.assertEqual(counted_types, {"Audio": 1})

    def test_multiple_of_one_file_type_counted(self) -> None:
        """Test when all files are of the same accepted file type."""
        counted_types = count_file_types(["file1.doc", "file2.doc", "file3.docx"])
        self.assertEqual(counted_types, {"Microsoft Word Document": 3})

    def test_multiple_different_files_counted(self) -> None:
        """Test when files span multiple accepted file types."""
        counted_types = count_file_types(
            ["file1.doc", "file2.doc", "song1.mp3", "song1.acc", "sheet1.xls", "sheet2.xlsx"],
        )
        self.assertEqual(
            counted_types,
            {
                "Microsoft Word Document": 2,
                "Audio": 2,
                "Microsoft Excel Spreadsheet": 2,
            },
        )

    def test_uppercase_extensions_are_counted(self) -> None:
        """Test that the file extension is case insensitive."""
        counted_types = count_file_types(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"],
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 4})

    def test_unaccepted_files_added_to_none(self) -> None:
        """Test when one file is accepted, and the rest are not found."""
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf", "file4.docx"],
        )
        self.assertEqual(
            counted_types,
            {
                "Microsoft Word Document": 1,
                None: 3,
            },
        )

    def test_no_files_human_readable(self) -> None:
        """Test that the statement is correct when no files are found."""
        statement = get_human_readable_file_count([])
        self.assertEqual(statement, "No file types could be identified")

    def test_no_accepted_file_types_human_readable(self) -> None:
        """Test that the statement is correct when no accepted files are found."""
        statement = get_human_readable_file_count(["file1.pages", "file2.docs", "file3.pdf"])
        self.assertEqual(statement, "No file types could be identified")

    def test_one_file_group_singular_human_readable(self) -> None:
        """Test that the statement is correct when one accepted file is found."""
        statement = get_human_readable_file_count(["file1.DOC"])
        self.assertEqual(statement, "1 Microsoft Word Document file")

    def test_one_file_group_plural_human_readable(self) -> None:
        """Test that the statement is correct when multiple accepted files are found in a group."""
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"]
        )
        self.assertEqual(statement, "4 Microsoft Word Document files")

    def test_three_groups_human_readable(self) -> None:
        """Test that the statement is correct when accepted files are found in three groups."""
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "song1.mp3", "img1.jpg", "img2.png", "img3.png"],
        )
        self.assertIn("2 Microsoft Word Document files", statement)
        self.assertIn("1 Audio file", statement)
        self.assertIn("3 Image files", statement)
