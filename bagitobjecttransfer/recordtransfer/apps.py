import logging
from pathlib import Path

from django.apps import AppConfig

from recordtransfer.settings import BAG_STORAGE_FOLDER


LOGGER = logging.getLogger(__name__)


class RecordTransferConfig(AppConfig):
    name = 'recordtransfer'

    def ready(self):
        bagging_area = Path(BAG_STORAGE_FOLDER)
        if not bagging_area.exists():
            LOGGER.warning(msg=('Bag storage folder {0} does not exist!'.format(
                str(BAG_STORAGE_FOLDER))))
