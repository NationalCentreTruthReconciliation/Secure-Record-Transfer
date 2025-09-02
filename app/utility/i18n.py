"""Utility functions concerning internationalization."""

from pathlib import Path

from django.conf import settings


def get_js_translation_version() -> str:
    """Return the latest modification time of all djangojs.mo files in the locale directory.

    This changes whenever compiled JS translations are updated.
    """
    return str(
        max(
            [
                item.stat().st_mtime
                for locale_dir in settings.LOCALE_PATHS
                for item in Path(locale_dir).rglob("djangojs.mo")
            ]
            or [0]
        )
    )
