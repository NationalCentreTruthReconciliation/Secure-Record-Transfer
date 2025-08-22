import logging
import mimetypes
import typing

from django.core.files import File

LOGGER = logging.getLogger(__name__)

try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None
    LOGGER.warning("Failed to import python-magic library. MIME type validation will be disabled.")


class Mime:
    """Guesses and checks MIME types."""

    MIME_TYPE_VARIATIONS: typing.ClassVar[dict[str, set[str]]] = {
        # Archive formats
        "zip": {"application/zip", "application/x-zip-compressed"},
        "7z": {"application/x-7z-compressed"},
        # Audio formats
        "mp3": {"audio/mpeg", "audio/mp3"},
        "wav": {"audio/wav", "audio/x-wav", "audio/wave"},
        "flac": {"audio/flac", "audio/x-flac"},
        # Document formats
        "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "odt": {"application/vnd.oasis.opendocument.text"},
        "pdf": {"application/pdf"},
        "txt": {"text/plain"},
        "html": {"text/html"},
        # Image formats
        "jpg": {"image/jpeg"},
        "jpeg": {"image/jpeg"},
        "png": {"image/png"},
        "gif": {"image/gif"},
        # Spreadsheet formats
        "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        "csv": {"text/csv", "text/plain", "application/csv"},
        # Video formats
        "mkv": {"video/x-matroska", "video/mkv"},
        "mp4": {"video/mp4"},
    }

    def __init__(self):
        self._type_cache: dict[str, set[str]] = {}

    def guess(self, extension: str) -> set[str]:
        """Get expected MIME types for a file extension using python-magic.

        Args:
            extension: File extension (e.g., '.pdf', 'jpg')

        Returns:
            set: Set of acceptable MIME types for the extension
        """
        # Normalize extension
        ext = extension.lower().lstrip(".")

        if ext in self._type_cache:
            return self._type_cache[ext]

        # Use mimetypes module for initial guess
        mime_type, _ = mimetypes.guess_type(f"file.{ext}")

        if not mime_type:
            return set()

        acceptable_types = {mime_type}

        if ext in self.MIME_TYPE_VARIATIONS:
            acceptable_types = acceptable_types.union(self.MIME_TYPE_VARIATIONS[ext])

        self._type_cache[ext] = acceptable_types
        return acceptable_types

    def check(self, file_object: File) -> str:
        """Check the file's MIME type.

        Args:
            file_object: The file to check the MIME type of.

        Returns:
            The MIME type, as a string
        """
        detected_mime_type = ""

        if magic is not None:
            # Read only first 2048 bytes to avoid memory issues
            file_chunk = file_object.read(2048)
            detected_mime_type = magic.from_buffer(file_chunk, mime=True)
            file_object.seek(0)
        else:
            raise Exception("magic library is not available")

        return detected_mime_type


mime = Mime()
