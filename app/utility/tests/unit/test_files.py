from typing import ClassVar
from unittest import TestCase

from utility.files import count_file_types, get_human_readable_file_count


class FileCountingUtilityTests(TestCase):
    """Test the count_file_types function."""

    accepted_formats: ClassVar[dict] = {
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

    def test_no_files_counted(self) -> None:
        """Test when an empty file list is used."""
        counted_types = count_file_types([], self.accepted_formats)
        self.assertEqual(counted_types, {})

    def test_no_accepted_file_types(self) -> None:
        """Test when there are no accepted file types used."""
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf"], self.accepted_formats
        )
        self.assertEqual(counted_types, {})

    def test_one_file_counted(self) -> None:
        """Test when there is one file used."""
        counted_types = count_file_types(["song1.mp3"], self.accepted_formats)
        self.assertEqual(counted_types, {"Audio": 1})

    def test_multiple_of_one_file_type_counted(self) -> None:
        """Test when there are multiple files of one type."""
        counted_types = count_file_types(
            ["file1.doc", "file2.doc", "file3.docx"], self.accepted_formats
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 3})

    def test_multiple_different_files_counted(self) -> None:
        """Test when there are multiple different files types."""
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

    def test_uppercase_extensions_are_counted(self) -> None:
        """Test that file counting is case-insensitive on the extension."""
        counted_types = count_file_types(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"], self.accepted_formats
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 4})

    def test_unaccepted_files_ignored(self) -> None:
        """Test when there are some valid, some invalid files."""
        counted_types = count_file_types(
            ["file1.pages", "file2.docs", "file3.pdf", "file4.docx"], self.accepted_formats
        )
        self.assertEqual(counted_types, {"Microsoft Word Document": 1})


class HumanReadableCountTests(TestCase):
    """Test the get_human_readable_file_count function."""

    accepted_formats: ClassVar[dict] = {
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

    def test_no_files_human_readable(self) -> None:
        """Test when there are no files."""
        statement = get_human_readable_file_count([], self.accepted_formats)
        self.assertEqual(statement, "No file types could be identified")

    def test_no_accepted_file_types_human_readable(self) -> None:
        """Test when there are no accepted file tpyes."""
        statement = get_human_readable_file_count(
            ["file1.pages", "file2.docs", "file3.pdf"], self.accepted_formats
        )
        self.assertEqual(statement, "No file types could be identified")

    def test_one_file_group_singular_human_readable(self) -> None:
        """Test when there is one accepted file."""
        statement = get_human_readable_file_count(["file1.DOC"], self.accepted_formats)
        self.assertEqual(statement, "1 Microsoft Word Document file")

    def test_one_file_group_plural_human_readable(self) -> None:
        """Test when there are multiple files in a group."""
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "file3.docx", "file4.DOCX"], self.accepted_formats
        )
        self.assertEqual(statement, "4 Microsoft Word Document files")

    def test_two_groups_human_readable(self) -> None:
        """Test when there are multiple files in multiple groups."""
        statement = get_human_readable_file_count(
            ["file1.DOC", "file2.doc", "song1.mp3", "img1.jpg", "img2.png", "img3.png"],
            self.accepted_formats,
        )
        self.assertIn("2 Microsoft Word Document files", statement)
        self.assertIn("1 Audio file", statement)
        self.assertIn("3 Image files", statement)
