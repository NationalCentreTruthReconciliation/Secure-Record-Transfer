import logging

import clamd

from django.core.exceptions import ValidationError

from . import settings
from . import connection


LOGGER = logging.getLogger('clamav')


def check_for_malware(file):
    ''' Scan the file for malware. If malware is found, a ValidationError is raised.

    If CLAMAV_ENABLED is False, return early.
    '''
    if not settings.CLAMAV_ENABLED:
        return

    socket = connection.get_clamd_socket()

    file.seek(0)

    try:
        output = socket.instream(file)
        status, reason = output['stream']

        if status != 'OK':
            LOGGER.warning('The given file contains Malware!')
            raise ValidationError(f'File contained malware. Reason: {reason}')

    except clamd.BufferTooLongError as exc:
        LOGGER.error('File is too large to be read by ClamAV! %d bytes were read', file.tell(), exc_info=exc)

    except clamd.ConnectionError as exc:
        LOGGER.error('ConnectionError occurred connecting to ClamAV!', exc_info=exc)

    # Return file pointer to beginning
    file.seek(0)
