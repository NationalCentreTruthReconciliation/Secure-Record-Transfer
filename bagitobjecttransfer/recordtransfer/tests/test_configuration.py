from django.test import TestCase

from recordtransfer.configuration import AcceptedFileTypes


class TestAcceptedFileTypeParser(TestCase):
    """Tests that the AcceptedFileTypes parser behaves as expected."""

    def test_value_error_if_none(self) -> None:
        """Test that a ValueError is thrown if None is passed to the parser."""
        parser = AcceptedFileTypes()
        self.assertRaises(ValueError, parser, None)

    def test_value_error_if_empty(self) -> None:
        """Test that a ValueError is thrown if an empty string is passed to the parser."""
        parser = AcceptedFileTypes()
        self.assertRaises(ValueError, parser, "")

    def test_value_error_if_invalid_group(self) -> None:
        """Test that a ValueError is thrown when a group is invalid."""
        parser = AcceptedFileTypes()

        values = ["Archive:?", "Spreadsheet:", "xlsx", "Image ; png,jpg"]

        for value in values:
            with self.subTest(value):
                self.assertRaises(ValueError, parser, value)

    def test_value_error_bad_extension(self) -> None:
        """Test that a ValueError is thrown when an extension is specified incorrectly."""
        parser = AcceptedFileTypes()
        self.assertRaises(ValueError, parser, "Image:-jpg")

    def test_value_error_extension_multiple(self) -> None:
        """Test that a ValueError is thrown when an extension appears in different groups."""
        parser = AcceptedFileTypes()
        # xlsx was specified twice
        self.assertRaises(ValueError, parser, "Excel Document:xlsx,xls|Spreadsheet:csv,xlsx")

    def test_single_group_parsed(self) -> None:
        """Test that a single file group gets parsed."""
        parser = AcceptedFileTypes()

        # These all get parsed to the same dictionary
        values = ["Image : jpg,png", "Image: JPG,PNG", "Image : .jpg,.png"]

        for value in values:
            with self.subTest(value):
                parsed = parser(value)
                self.assertEqual(parsed, {"Image": {"jpg", "png"}})

    def test_multiple_groups_parsed(self) -> None:
        """Test that multiple groups get parsed."""
        parser = AcceptedFileTypes()

        parsed = parser("Archive:zip,7z,rar|Document:doc,docx|Digital Photo:jpg,jpeg,tiff")

        self.assertEqual(
            parsed,
            {
                "Archive": {"zip", "7z", "rar"},
                "Document": {"doc", "docx"},
                "Digital Photo": {"jpg", "jpeg", "tiff"},
            },
        )

    def test_multiple_group_combined(self) -> None:
        """Test that file types are combined if a group is defined multiple times."""
        parser = AcceptedFileTypes()
        parsed = parser("Image:png|Image:jpg|Image:gif")
        self.assertEqual(parsed, {"Image": {"png", "jpg", "gif"}})
