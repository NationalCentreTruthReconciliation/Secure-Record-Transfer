import logging
from typing import BinaryIO, cast

from clamav_client import clamd
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from . import connection, settings

LOGGER = logging.getLogger("clamav")


def check_for_malware(file: UploadedFile) -> None:
    """Scan the file for malware. If malware is found, a ValidationError is raised.

    If CLAMAV_ENABLED is False, return early.
    """
    if not settings.CLAMAV_ENABLED:
        return

    socket = connection.get_clamd_socket()

    if not socket:
        raise ConnectionError("Connection to ClamAV could not be established.")

    file.seek(0)

    try:
        output = socket.instream(cast(BinaryIO, file))
        status, reason = output["stream"]

        if status != "OK":
            LOGGER.warning(
                "The given file contains Malware! Status: %s, Reason: %s", status, reason
            )
            raise ValidationError(f"File contained malware. Reason: {reason}")

    except clamd.BufferTooLongError as exc:
        LOGGER.error(
            "File is too large to be read by ClamAV! %d bytes were read", file.tell(), exc_info=exc
        )

    except clamd.CommunicationError as exc:
        LOGGER.error("CommunicationError occurred connecting to ClamAV!", exc_info=exc)

    # Return file pointer to beginning
    file.seek(0)
