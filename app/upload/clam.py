"""Malware and virus scanning with ClamAV."""

import logging
from typing import BinaryIO, Optional, cast

from clamav_client import clamd
from django.core.exceptions import ValidationError
from django.core.files import File

from . import settings

LOGGER = logging.getLogger(__name__)


def get_clamd_socket() -> Optional[clamd.ClamdNetworkSocket]:
    """Return a socket that can be used to communicate with clamd over the network.

    Returns:
        None if :ref:`CLAMAV_ENABLED` is False, otherwise, the connection object
    """
    if not settings.CLAMAV_ENABLED:
        return None
    return clamd.ClamdNetworkSocket(settings.CLAMAV_HOST, settings.CLAMAV_PORT)


def check_for_malware(file: File) -> None:
    """Scan the file for malware.

    If :ref:`CLAMAV_ENABLED` is False, return early.

    Raises:
        ValidationError: If the file contains malware.
        ConnectionError: If the connection to ClamAV cannot be established or if there is a
            communication error.
        ValueError: If the file is too large to be scanned.
    """
    if not settings.CLAMAV_ENABLED:
        return

    socket = get_clamd_socket()

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
        raise ValueError("File is too large to scan for malware") from exc

    except clamd.CommunicationError as exc:
        LOGGER.error("CommunicationError occurred connecting to ClamAV!", exc_info=exc)
        raise ConnectionError(
            "Unable to scan file for malware due to scanner communication error"
        ) from exc

    # Return file pointer to beginning
    file.seek(0)
