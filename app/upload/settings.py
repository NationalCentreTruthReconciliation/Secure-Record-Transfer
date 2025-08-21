"""upload app settings."""

from django.conf import settings

from ..configuration import AcceptedFileTypes

FILE_UPLOAD_ENABLED = getattr(settings, "FILE_UPLOAD_ENABLED", True)

MAX_TOTAL_UPLOAD_SIZE_MB = getattr(settings, "MAX_TOTAL_UPLOAD_SIZE_MB", 256)
MAX_SINGLE_UPLOAD_SIZE_MB = getattr(settings, "MAX_SINGLE_UPLOAD_SIZE_MB", 64)
MAX_TOTAL_UPLOAD_COUNT = getattr(settings, "MAX_TOTAL_UPLOAD_COUNT", 40)

ACCEPTED_FILE_FORMATS = getattr(
    settings,
    "ACCEPTED_FILE_TYPES",
    AcceptedFileTypes()(
        "Audio:mp3,wav,flac|Document:docx,odt,pdf,txt,html|Image:jpg,jpeg,png,gif|Spreadsheet:xlsx,csv|Video:mkv,mp4"
    ),
)
