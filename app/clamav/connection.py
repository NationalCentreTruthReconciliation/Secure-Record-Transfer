from typing import Optional

from clamav_client import clamd

from . import settings


def get_clamd_socket() -> Optional[clamd.ClamdNetworkSocket]:
    """Return a socket that can be used to communicate with clamd over the network.

    Returns:
        None if :ref:`CLAMAV_ENABLED` is False, otherwise, the connection object
    """
    if not settings.CLAMAV_ENABLED:
        return None
    return clamd.ClamdNetworkSocket(settings.CLAMAV_HOST, settings.CLAMAV_PORT)
