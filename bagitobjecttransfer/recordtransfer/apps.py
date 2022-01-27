import logging
import os

from django.apps import AppConfig

from recordtransfer.settings import BAG_STORAGE_FOLDER, UPLOAD_STORAGE_FOLDER


LOGGER = logging.getLogger(__name__)


class RecordTransferConfig(AppConfig):
    name = 'recordtransfer'

    def ready(self):
        create_directories = [
            ('BAG_STORAGE_FOLDER', BAG_STORAGE_FOLDER),
            ('UPLOAD_STORAGE_FOLDER', UPLOAD_STORAGE_FOLDER),
        ]

        for name, directory in create_directories:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                os.mkdir(directory)
                LOGGER.info(msg=('Created {0} at {1}'.format(name, directory)))
