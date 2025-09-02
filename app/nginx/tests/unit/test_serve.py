from django.test import TestCase, override_settings
from nginx.serve import serve_media_file


class ServeMediaFileTests(TestCase):
    """Tests the serve function."""

    @override_settings(DEBUG=True)
    def test_debug_mode(self) -> None:
        """Test that a re-direct is returned when DEBUG mode is on."""
        file_url = "/media/temp/aaa/file.pdf"
        response = serve_media_file(file_url)
        self.assertTrue(hasattr(response, "url"))
        self.assertEqual(response.url, file_url)

    @override_settings(DEBUG=False)
    def test_prod_mode(self) -> None:
        """Test that an X-Accel-Redirect is returned when DEBUG mode is off."""
        file_url = "/media/temp/aaa/file.pdf"
        response = serve_media_file(file_url)
        self.assertFalse(hasattr(response, "url"))
        self.assertEqual(response["X-Accel-Redirect"], file_url)

    @override_settings(DEBUG=False)
    def test_prod_mode_zip_file(self) -> None:
        """Test that proper content type headers are returned if the file is a .zip file."""
        file_url = "/media/temp/aaa/file.zip"
        response = serve_media_file(file_url)
        self.assertFalse(hasattr(response, "url"))
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="file.zip"')
        self.assertEqual(response["X-Accel-Redirect"], file_url)
