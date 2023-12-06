from typing import Optional

import clamd

from . import settings


def get_clamd_socket() -> Optional[clamd.ClamdNetworkSocket]:
    ''' Return a socket that can be used to communicate with clamd over the network.

    Returns:
        (Optional[clamd.ClamdNetworkSocket]):
            None if CLAMAV_ENABLED is False, otherwise, the connection object
    '''
    if not settings.CLAMAV_ENABLED:
        return None
    return clamd.ClamdNetworkSocket(settings.CLAMAV_HOST, settings.CLAMAV_PORT)


def test_connection() -> bool:
    ''' Test whether Clamd can be connected to over the network.

    Returns:
        (bool): True if connection is OK, False if connection could not be made
    '''
    if not settings.CLAMAV_ENABLED:
        return True
    try:
        get_clamd_socket().ping()
        return True
    except clamd.ClamdError:
        return False
