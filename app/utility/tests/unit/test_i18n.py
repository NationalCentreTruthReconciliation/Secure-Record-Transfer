from unittest import TestCase

from django.test import override_settings
from utility.i18n import get_js_translation_version


class TestGetJsTranslationVersion(TestCase):
    """Tests for get_js_translation_version."""

    @override_settings(LOCALE_PATHS=[])
    def test_no_locale_paths(self) -> None:
        """Test that a default value of '0' is returned if there are no paths."""
        version = get_js_translation_version()
        self.assertEqual("0", version)
