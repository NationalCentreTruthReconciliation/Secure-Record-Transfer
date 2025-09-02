from unittest import TestCase

from utility.strings import html_to_text


class HtmlToTextTests(TestCase):
    """Test the html_to_text function."""

    def test_empty_string(self) -> None:
        """Test when an empty string is used."""
        text = html_to_text("")
        self.assertEqual(text, "")

    def test_simple_tag_removal(self) -> None:
        """Test when only one tag is present."""
        text = html_to_text("<h1>Hello</h1>")
        self.assertEqual(text, "Hello")

    def test_nested_tags(self) -> None:
        """Test when multiple nested tags are present."""
        text = html_to_text("<div><div><p>Hello</p></div></div>")
        self.assertEqual(text, "Hello")

    def test_whitespace_stripped(self) -> None:
        """Test that whitespace is removed."""
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
