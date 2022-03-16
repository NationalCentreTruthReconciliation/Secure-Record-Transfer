import logging
import os

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

from bagit import CHECKSUM_ALGOS

from recordtransfer import settings


LOGGER = logging.getLogger(__name__)


class RecordTransferConfig(AppConfig):
    ''' Top-level application config for the recordtransfer app
    '''

    name = 'recordtransfer'

    def ready(self):
        if not settings.BAG_CHECKSUMS:
            raise ImproperlyConfigured(
                'No checksums found in the BAG_CHECKSUMS setting! Choose one '
                'or more checksum algorithms to generate checksums for when '
                'creating a BagIt bag, separated by commas (i.e., "sha1,sha256")'
            )
        not_found = [a for a in settings.BAG_CHECKSUMS if a not in CHECKSUM_ALGOS]
        if not_found:
            not_supported = ', '.join(not_found)
            supported = ', '.join(CHECKSUM_ALGOS)
            raise ImproperlyConfigured((
                'These algorithm(s) found in the BAG_CHECKSUMS setting are NOT '
                'supported: {0}. The algorithms that ARE supported are: {1}.'
            ).format(not_supported, supported))

        create_directories = [
            ('BAG_STORAGE_FOLDER', settings.BAG_STORAGE_FOLDER),
            ('UPLOAD_STORAGE_FOLDER', settings.UPLOAD_STORAGE_FOLDER),
        ]
        for name, directory in create_directories:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                os.mkdir(directory)
                LOGGER.info(msg=('Created {0} at {1}'.format(name, directory)))
