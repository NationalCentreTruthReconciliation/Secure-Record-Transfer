"""upload app settings."""

from django.conf import settings

FILE_UPLOAD_ENABLED = getattr(settings, "FILE_UPLOAD_ENABLED", True)

MAX_TOTAL_UPLOAD_SIZE_MB = getattr(settings, "MAX_TOTAL_UPLOAD_SIZE_MB", 256)
MAX_SINGLE_UPLOAD_SIZE_MB = getattr(settings, "MAX_SINGLE_UPLOAD_SIZE_MB", 64)
MAX_TOTAL_UPLOAD_COUNT = getattr(settings, "MAX_TOTAL_UPLOAD_COUNT", 40)

# This needs to be set
ACCEPTED_FILE_FORMATS = settings.ACCEPTED_FILE_FORMATS

CLAMAV_ENABLED = getattr(settings, "CLAMAV_ENABLED", True)
CLAMAV_HOST = getattr(settings, "CLAMAV_HOST", "clamav")
CLAMAV_PORT = getattr(settings, "CLAMAV_PORT", 3310)
