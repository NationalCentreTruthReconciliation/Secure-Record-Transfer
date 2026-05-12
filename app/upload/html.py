from pathlib import Path

import nh3
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile


def is_html_file(file: UploadedFile) -> bool:
    """Check if a file is an HTML file or not."""
    file_extension = Path(file.name).suffix.lower()
    return file_extension in (".htm", ".html") and file.content_type == "text/html"


def sanitize_html_file(file: UploadedFile) -> UploadedFile:
    """Sanitize uploaded HTML files using nh3.

    HTML file content is sanitized so unsafe content, including script tags, is removed before the
    file is saved.

    Non-HTML files are returned as-is.
    """
    if not is_html_file(file):
        return file

    charset = file.charset or "utf-8"
    file.seek(0)
    content = file.read().decode(charset, errors="replace")
    sanitized_content = nh3.clean(content).encode(charset)

    sanitized_file = SimpleUploadedFile(
        file.name,
        sanitized_content,
        content_type="text/html",
    )
    sanitized_file.charset = file.charset
    return sanitized_file
